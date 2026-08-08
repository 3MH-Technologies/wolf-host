import asyncio
from datetime import datetime, timezone
from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.bot import Bot, BotStatus
from app.models.payment import Invoice, PaymentStatus
from app.models.plan import Subscription, SubscriptionStatus
from app.services.docker_engine import docker_engine


async def _monitor_bots_health() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Bot).where(Bot.status == BotStatus.RUNNING, Bot.auto_restart == True))
        bots = result.scalars().all()
        for bot in bots:
            docker_status = await docker_engine.get_status(bot.container_name)
            if docker_status in ("exited", "not_found"):
                bot.status = BotStatus.CRASHED
                bot.restart_count += 1
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
                except Exception as exc:
                    bot.status = BotStatus.ERROR
                    bot.last_error = str(exc)
                await db.commit()


async def _expire_pending_invoices() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Invoice).where(Invoice.status == PaymentStatus.PENDING, Invoice.expires_at < datetime.now(timezone.utc))
        )
        for invoice in result.scalars().all():
            invoice.status = PaymentStatus.EXPIRED
        await db.commit()


async def _expire_subscriptions() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Subscription).where(Subscription.status == SubscriptionStatus.ACTIVE, Subscription.ends_at < datetime.now(timezone.utc))
        )
        for subscription in result.scalars().all():
            subscription.status = SubscriptionStatus.EXPIRED
        await db.commit()


@celery_app.task(name="app.workers.tasks.monitor_bots_health")
def monitor_bots_health() -> None:
    asyncio.run(_monitor_bots_health())


@celery_app.task(name="app.workers.tasks.expire_pending_invoices")
def expire_pending_invoices() -> None:
    asyncio.run(_expire_pending_invoices())


@celery_app.task(name="app.workers.tasks.expire_subscriptions")
def expire_subscriptions() -> None:
    asyncio.run(_expire_subscriptions())
