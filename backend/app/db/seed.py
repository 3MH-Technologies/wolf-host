import asyncio
import os
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.plan import Plan, PlanTier
from app.models.user import User, UserRole
from app.core.security import hash_password

DEFAULT_PLANS = [
    dict(tier=PlanTier.FREE, name="Free", price_monthly=0, max_bots=1, max_containers=1, cpu_limit=0.25, ram_limit_mb=128, storage_limit_mb=256, process_limit=16, bandwidth_limit_mb=1024),
    dict(tier=PlanTier.BASIC, name="Basic", price_monthly=5, max_bots=3, max_containers=3, cpu_limit=0.5, ram_limit_mb=256, storage_limit_mb=1024, process_limit=32, bandwidth_limit_mb=5120),
    dict(tier=PlanTier.PRO, name="Pro", price_monthly=15, max_bots=10, max_containers=10, cpu_limit=1.0, ram_limit_mb=512, storage_limit_mb=5120, process_limit=64, bandwidth_limit_mb=20480),
    dict(tier=PlanTier.ENTERPRISE, name="Enterprise", price_monthly=50, max_bots=50, max_containers=50, cpu_limit=2.0, ram_limit_mb=2048, storage_limit_mb=20480, process_limit=128, bandwidth_limit_mb=102400),
]


async def seed_plans() -> None:
    async with AsyncSessionLocal() as db:
        for plan_data in DEFAULT_PLANS:
            result = await db.execute(select(Plan).where(Plan.tier == plan_data["tier"]))
            if result.scalar_one_or_none() is None:
                db.add(Plan(**plan_data))
        await db.commit()


async def seed_admin() -> None:
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        return
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == admin_email))
        if result.scalar_one_or_none() is None:
            db.add(User(
                email=admin_email,
                username="admin",
                hashed_password=hash_password(admin_password),
                role=UserRole.SUPER_ADMIN,
                is_verified=True,
            ))
            await db.commit()


async def main() -> None:
    await seed_plans()
    await seed_admin()


if __name__ == "__main__":
    asyncio.run(main())
