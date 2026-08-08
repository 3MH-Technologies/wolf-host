import uuid
import re
import secrets
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.models.bot import Bot, BotStatus, BotSourceType
from app.models.user import User
from app.models.plan import Plan
from app.services.docker_engine import docker_engine, DockerEngineError
from app.services.file_manager import FileManager, FileManagerError


class BotServiceError(Exception):
    pass


def slugify(name: str, owner_id: uuid.UUID) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{base}-{str(owner_id)[:8]}-{secrets.token_hex(3)}"


class BotService:
    async def get_user_plan(self, db: AsyncSession, user: User) -> Plan:
        if user.plan_id is None:
            result = await db.execute(select(Plan).where(Plan.tier == "free"))
        else:
            result = await db.execute(select(Plan).where(Plan.id == user.plan_id))
        plan = result.scalar_one_or_none()
        if plan is None:
            raise BotServiceError("plan_not_found")
        return plan

    async def enforce_bot_quota(self, db: AsyncSession, user: User) -> None:
        plan = await self.get_user_plan(db, user)
        count_result = await db.execute(select(func.count(Bot.id)).where(Bot.owner_id == user.id))
        current_count = count_result.scalar_one()
        if current_count >= plan.max_bots:
            raise BotServiceError("bot_quota_exceeded")

    async def create_bot(
        self, db: AsyncSession, user: User, name: str, source_type: BotSourceType,
        entrypoint: str, git_url: str | None = None,
    ) -> Bot:
        await self.enforce_bot_quota(db, user)
        plan = await self.get_user_plan(db, user)

        slug = slugify(name, user.id)
        storage_path = str(Path(settings.BOTS_STORAGE_PATH) / str(user.id) / slug)

        bot = Bot(
            owner_id=user.id,
            name=name,
            slug=slug,
            source_type=source_type,
            git_url=git_url,
            entrypoint=entrypoint,
            container_name=f"wolfhost-bot-{slug}",
            storage_path=storage_path,
            cpu_limit=float(plan.cpu_limit),
            ram_limit_mb=plan.ram_limit_mb,
            disk_limit_mb=plan.storage_limit_mb,
            process_limit=plan.process_limit,
        )
        db.add(bot)
        await db.flush()

        fm = FileManager(storage_path)
        fm.ensure_root()

        await db.commit()
        return bot

    async def get_owned_bot(self, db: AsyncSession, user: User, bot_id: uuid.UUID) -> Bot:
        result = await db.execute(select(Bot).where(Bot.id == bot_id, Bot.owner_id == user.id))
        bot = result.scalar_one_or_none()
        if bot is None:
            raise BotServiceError("bot_not_found")
        return bot

    async def start_bot(self, db: AsyncSession, bot: Bot) -> Bot:
        fm = FileManager(bot.storage_path)
        requirements = fm.detect_requirements()
        req_path = Path(bot.storage_path) / "requirements.txt"
        if requirements and not req_path.exists():
            req_path.write_text("\n".join(requirements))

        bot.status = BotStatus.INSTALLING
        await db.commit()

        try:
            container_id = await docker_engine.create_and_start(
                container_name=bot.container_name,
                host_bot_path=bot.storage_path,
                entrypoint=bot.entrypoint,
                env_vars=bot.env_vars or {},
                cpu_limit=bot.cpu_limit,
                ram_limit_mb=bot.ram_limit_mb,
                disk_limit_mb=bot.disk_limit_mb,
                process_limit=bot.process_limit,
            )
            bot.container_id = container_id
            bot.status = BotStatus.RUNNING
            bot.last_error = None
        except DockerEngineError as exc:
            bot.status = BotStatus.ERROR
            bot.last_error = str(exc)
        await db.commit()
        return bot

    async def stop_bot(self, db: AsyncSession, bot: Bot) -> Bot:
        await docker_engine.stop(bot.container_name)
        bot.status = BotStatus.STOPPED
        await db.commit()
        return bot

    async def restart_bot(self, db: AsyncSession, bot: Bot) -> Bot:
        try:
            await docker_engine.restart(bot.container_name)
            bot.status = BotStatus.RUNNING
            bot.restart_count += 1
        except DockerEngineError:
            return await self.start_bot(db, bot)
        await db.commit()
        return bot

    async def delete_bot(self, db: AsyncSession, bot: Bot) -> None:
        await docker_engine.remove_if_exists(bot.container_name)
        fm = FileManager(bot.storage_path)
        try:
            fm.delete("")
        except (FileManagerError, FileNotFoundError):
            pass
        await db.delete(bot)
        await db.commit()

    async def sync_status(self, db: AsyncSession, bot: Bot) -> Bot:
        docker_status = await docker_engine.get_status(bot.container_name)
        mapping = {
            "running": BotStatus.RUNNING,
            "exited": BotStatus.CRASHED if bot.status == BotStatus.RUNNING else BotStatus.STOPPED,
            "created": BotStatus.CREATED,
            "not_found": bot.status,
        }
        new_status = mapping.get(docker_status, bot.status)
        if new_status != bot.status:
            bot.status = new_status
            await db.commit()
        return bot


bot_service = BotService()
