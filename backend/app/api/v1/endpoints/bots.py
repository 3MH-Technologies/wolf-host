import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.bot import Bot
from app.schemas.bot import (
    BotCreateRequest, BotResponse, BotEnvUpdateRequest, BotStatsResponse,
    FileEntry, FileWriteRequest, FileRenameRequest, FileMoveRequest,
)
from app.core.dependencies import get_current_user, get_client_ip
from app.core.config import settings
from app.services.bot_service import bot_service, BotServiceError
from app.services.docker_engine import docker_engine
from app.services.file_manager import FileManager, FileManagerError
from app.services.audit_service import log_action

router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(payload: BotCreateRequest, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        bot = await bot_service.create_bot(db, user, payload.name, payload.source_type, payload.entrypoint, payload.git_url)
    except BotServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await log_action(db, user.id, "bot.create", "bot", str(bot.id), get_client_ip(request), request.headers.get("user-agent", ""))
    return bot


@router.get("", response_model=list[BotResponse])
async def list_bots(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bot).where(Bot.owner_id == user.id).order_by(Bot.created_at.desc()))
    return result.scalars().all()


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        bot = await bot_service.get_owned_bot(db, user, bot_id)
    except BotServiceError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="bot_not_found")
    return await bot_service.sync_status(db, bot)


@router.post("/{bot_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_bot_file(bot_id: uuid.UUID, file: UploadFile = File(...), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file_too_large")

    fm = FileManager(bot.storage_path)
    try:
        if file.filename.endswith(".zip"):
            zip_path = await fm.save_upload(file.filename, content)
            fm.extract_zip(zip_path)
        else:
            await fm.save_upload(file.filename, content)
    except FileManagerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"message": "uploaded"}


@router.post("/{bot_id}/start", response_model=BotResponse)
async def start_bot(bot_id: uuid.UUID, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    bot = await bot_service.start_bot(db, bot)
    await log_action(db, user.id, "bot.start", "bot", str(bot.id), get_client_ip(request), request.headers.get("user-agent", ""))
    return bot


@router.post("/{bot_id}/stop", response_model=BotResponse)
async def stop_bot(bot_id: uuid.UUID, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    bot = await bot_service.stop_bot(db, bot)
    await log_action(db, user.id, "bot.stop", "bot", str(bot.id), get_client_ip(request), request.headers.get("user-agent", ""))
    return bot


@router.post("/{bot_id}/restart", response_model=BotResponse)
async def restart_bot(bot_id: uuid.UUID, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    bot = await bot_service.restart_bot(db, bot)
    await log_action(db, user.id, "bot.restart", "bot", str(bot.id), get_client_ip(request), request.headers.get("user-agent", ""))
    return bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(bot_id: uuid.UUID, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    await bot_service.delete_bot(db, bot)
    await log_action(db, user.id, "bot.delete", "bot", str(bot_id), get_client_ip(request), request.headers.get("user-agent", ""))
    return None


@router.put("/{bot_id}/env", response_model=BotResponse)
async def update_env(bot_id: uuid.UUID, payload: BotEnvUpdateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    bot.env_vars = payload.env_vars
    await db.commit()
    return bot


@router.get("/{bot_id}/logs")
async def get_logs(bot_id: uuid.UUID, tail: int = 500, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    logs = await docker_engine.get_logs(bot.container_name, tail=tail)
    return {"logs": logs}


@router.get("/{bot_id}/logs/stream")
async def stream_logs(bot_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)

    async def generator():
        async for line in docker_engine.stream_logs(bot.container_name):
            yield f"data: {line}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")


@router.get("/{bot_id}/stats", response_model=BotStatsResponse)
async def get_stats(bot_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    stats = await docker_engine.get_stats(bot.container_name)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="container_not_running")
    return stats


@router.get("/{bot_id}/files", response_model=list[FileEntry])
async def list_files(bot_id: uuid.UUID, path: str = "", user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    fm = FileManager(bot.storage_path)
    try:
        return fm.list_dir(path)
    except FileManagerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{bot_id}/files/content")
async def read_file(bot_id: uuid.UUID, path: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    fm = FileManager(bot.storage_path)
    try:
        return {"content": fm.read_text_file(path)}
    except FileManagerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/{bot_id}/files/content")
async def write_file(bot_id: uuid.UUID, path: str, payload: FileWriteRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    fm = FileManager(bot.storage_path)
    try:
        await fm.write_text_file(path, payload.content)
    except FileManagerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"message": "saved"}


@router.delete("/{bot_id}/files")
async def delete_file(bot_id: uuid.UUID, path: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    fm = FileManager(bot.storage_path)
    try:
        fm.delete(path)
    except FileManagerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"message": "deleted"}


@router.post("/{bot_id}/files/rename")
async def rename_file(bot_id: uuid.UUID, path: str, payload: FileRenameRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    fm = FileManager(bot.storage_path)
    try:
        fm.rename(path, payload.new_name)
    except FileManagerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"message": "renamed"}


@router.post("/{bot_id}/files/move")
async def move_file(bot_id: uuid.UUID, path: str, payload: FileMoveRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    fm = FileManager(bot.storage_path)
    try:
        fm.move(path, payload.destination)
    except FileManagerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"message": "moved"}


ALLOWED_CONSOLE_COMMANDS = {"ls", "pwd", "cat", "python", "pip", "ps", "df", "whoami", "echo"}


@router.post("/{bot_id}/console")
async def run_console_command(bot_id: uuid.UUID, command: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bot = await _get_bot_or_404(db, user, bot_id)
    parts = command.strip().split()
    if not parts or parts[0] not in ALLOWED_CONSOLE_COMMANDS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="command_not_allowed")
    result = await docker_engine.exec_command(bot.container_name, parts)
    return result


async def _get_bot_or_404(db: AsyncSession, user: User, bot_id: uuid.UUID) -> Bot:
    try:
        return await bot_service.get_owned_bot(db, user, bot_id)
    except BotServiceError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="bot_not_found")
