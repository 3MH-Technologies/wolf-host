import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.session import UserSession, ApiKey
from app.models.audit import Notification
from app.core.dependencies import get_current_user
from app.core.security import hash_password, verify_password, generate_api_key

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id), "email": user.email, "username": user.username,
        "role": user.role.value, "totp_enabled": user.totp_enabled, "created_at": user.created_at,
    }


@router.put("/me/password")
async def change_password(current_password: str, new_password: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="incorrect_current_password")
    user.hashed_password = hash_password(new_password)
    await db.commit()
    return {"message": "password_updated"}


@router.get("/me/sessions")
async def list_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSession).where(UserSession.user_id == user.id, UserSession.is_revoked == False))
    sessions = result.scalars().all()
    return [
        {"id": str(s.id), "ip_address": s.ip_address, "device_label": s.device_label,
         "created_at": s.created_at, "last_used_at": s.last_used_at}
        for s in sessions
    ]


@router.delete("/me/sessions/{session_id}")
async def revoke_session(session_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserSession).where(UserSession.id == session_id, UserSession.user_id == user.id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session_not_found")
    session.is_revoked = True
    await db.commit()
    return {"message": "session_revoked"}


@router.post("/me/api-keys")
async def create_api_key(name: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    raw_key = generate_api_key()
    api_key = ApiKey(user_id=user.id, name=name, key_prefix=raw_key[:10], key_hash=hash_password(raw_key))
    db.add(api_key)
    await db.commit()
    return {"api_key": raw_key, "message": "store_this_key_it_will_not_be_shown_again"}


@router.get("/me/api-keys")
async def list_api_keys(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey).where(ApiKey.user_id == user.id))
    keys = result.scalars().all()
    return [{"id": str(k.id), "name": k.name, "key_prefix": k.key_prefix, "is_active": k.is_active, "created_at": k.created_at} for k in keys]


@router.delete("/me/api-keys/{key_id}")
async def revoke_api_key(key_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user.id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="key_not_found")
    api_key.is_active = False
    await db.commit()
    return {"message": "key_revoked"}


@router.get("/me/notifications")
async def list_notifications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50))
    notifications = result.scalars().all()
    return [{"id": str(n.id), "title": n.title, "message": n.message, "is_read": n.is_read, "created_at": n.created_at} for n in notifications]


@router.put("/me/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id, Notification.user_id == user.id))
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="notification_not_found")
    notification.is_read = True
    await db.commit()
    return {"message": "marked_read"}
