import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.bot import Bot, BotStatus
from app.models.payment import Invoice, PaymentStatus
from app.models.payment import Coupon
from app.schemas.bot import BotResponse
from app.core.dependencies import get_current_admin
from app.services.bot_service import bot_service
from app.services.docker_engine import docker_engine

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_platform_stats(admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    users_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    bots_count = (await db.execute(select(func.count(Bot.id)))).scalar_one()
    running_bots = (await db.execute(select(func.count(Bot.id)).where(Bot.status == BotStatus.RUNNING))).scalar_one()
    revenue = (await db.execute(select(func.coalesce(func.sum(Invoice.amount), 0)).where(Invoice.status == PaymentStatus.PAID))).scalar_one()
    return {
        "total_users": users_count,
        "total_bots": bots_count,
        "running_bots": running_bots,
        "total_revenue": float(revenue),
    }


@router.get("/users")
async def list_all_users(admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {"id": str(u.id), "email": u.email, "username": u.username, "role": u.role.value,
         "is_active": u.is_active, "is_suspended": u.is_suspended, "created_at": u.created_at}
        for u in users
    ]


@router.post("/users/{user_id}/suspend")
async def suspend_user(user_id: uuid.UUID, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    target.is_suspended = True
    await db.commit()
    return {"message": "user_suspended"}


@router.post("/users/{user_id}/unsuspend")
async def unsuspend_user(user_id: uuid.UUID, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    target.is_suspended = False
    await db.commit()
    return {"message": "user_unsuspended"}


@router.get("/bots", response_model=list[BotResponse])
async def list_all_bots(admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bot).order_by(Bot.created_at.desc()))
    return result.scalars().all()


@router.post("/bots/{bot_id}/force-stop")
async def force_stop_bot(bot_id: uuid.UUID, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="bot_not_found")
    await bot_service.stop_bot(db, bot)
    return {"message": "bot_stopped"}


@router.delete("/bots/{bot_id}/force-delete")
async def force_delete_bot(bot_id: uuid.UUID, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="bot_not_found")
    await bot_service.delete_bot(db, bot)
    return {"message": "bot_deleted"}


@router.post("/coupons")
async def create_coupon(code: str, discount_percent: int, max_uses: int = 1, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    if discount_percent < 1 or discount_percent > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_discount")
    coupon = Coupon(code=code, discount_percent=discount_percent, max_uses=max_uses)
    db.add(coupon)
    await db.commit()
    return {"message": "coupon_created", "id": str(coupon.id)}


@router.get("/docker/containers")
async def list_docker_containers(admin: User = Depends(get_current_admin)):
    containers = await docker_engine._run_sync(docker_engine._client.containers.list, all=True, filters={"label": "managed-by=wolfhost"})
    return [{"id": c.id, "name": c.name, "status": c.status} for c in containers]
