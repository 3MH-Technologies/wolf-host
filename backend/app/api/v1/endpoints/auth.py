import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.session import UserSession
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest,
    ForgotPasswordRequest, ResetPasswordRequest, Enable2FAResponse, Verify2FARequest,
)
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, generate_totp_secret, get_totp_uri, verify_totp, generate_secure_token,
)
from app.core.dependencies import get_current_user, get_client_ip
from app.services.email_service import send_password_reset_email
from app.services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where((User.email == payload.email) | (User.username == payload.username)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_or_username_taken")

    user = User(email=payload.email, username=payload.username, hashed_password=hash_password(payload.password))
    db.add(user)
    await db.flush()

    session = await _create_session(db, user.id, request)
    await db.commit()

    await log_action(db, user.id, "user.register", "user", str(user.id), get_client_ip(request), request.headers.get("user-agent", ""))

    access_token = create_access_token(str(user.id), {"role": user.role.value})
    refresh_token = create_refresh_token(str(user.id), str(session.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    if user.is_suspended or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account_disabled")

    if user.totp_enabled:
        if not payload.totp_code or not verify_totp(user.totp_secret, payload.totp_code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="totp_required_or_invalid")

    session = await _create_session(db, user.id, request)
    await db.commit()

    await log_action(db, user.id, "user.login", "user", str(user.id), get_client_ip(request), request.headers.get("user-agent", ""))

    access_token = create_access_token(str(user.id), {"role": user.role.value})
    refresh_token = create_refresh_token(str(user.id), str(session.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_refresh_token")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token_type")

    session_id = decoded.get("sid")
    result = await db.execute(select(UserSession).where(UserSession.id == uuid.UUID(session_id)))
    session = result.scalar_one_or_none()

    if session is None or session.is_revoked or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session_expired")

    user_result = await db.execute(select(User).where(User.id == session.user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active or user.is_suspended:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_inactive")

    session.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(str(user.id), {"role": user.role.value})
    new_refresh_token = create_refresh_token(str(user.id), str(session.id))
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
        session_id = decoded.get("sid")
        result = await db.execute(select(UserSession).where(UserSession.id == uuid.UUID(session_id)))
        session = result.scalar_one_or_none()
        if session:
            session.is_revoked = True
            await db.commit()
    except (ValueError, TypeError):
        pass
    return None


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user:
        reset_token = create_access_token(str(user.id), {"type_override": "password_reset"})
        await send_password_reset_email(user.email, reset_token)
    return {"message": "if_account_exists_email_sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded = decode_token(payload.token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_or_expired_token")

    user_id = decoded.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_token")

    user.hashed_password = hash_password(payload.new_password)
    await db.execute(UserSession.__table__.update().where(UserSession.user_id == user.id).values(is_revoked=True))
    await db.commit()
    return {"message": "password_updated"}


@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = generate_totp_secret()
    user.totp_secret = secret
    await db.commit()
    return Enable2FAResponse(secret=secret, otpauth_uri=get_totp_uri(secret, user.email))


@router.post("/2fa/verify", status_code=status.HTTP_200_OK)
async def verify_2fa(payload: Verify2FARequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not user.totp_secret or not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_code")
    user.totp_enabled = True
    await db.commit()
    return {"message": "2fa_enabled"}


@router.post("/2fa/disable", status_code=status.HTTP_200_OK)
async def disable_2fa(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.totp_enabled = False
    user.totp_secret = None
    await db.commit()
    return {"message": "2fa_disabled"}


async def _create_session(db: AsyncSession, user_id: uuid.UUID, request: Request) -> UserSession:
    session = UserSession(
        user_id=user_id,
        refresh_token_hash=generate_secure_token(16),
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent", "unknown")[:512],
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(session)
    await db.flush()
    return session
