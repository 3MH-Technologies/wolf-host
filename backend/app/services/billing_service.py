import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import stripe
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.payment import Invoice, PaymentProvider, PaymentStatus, Coupon
from app.models.plan import Plan, Subscription, SubscriptionStatus
from app.models.user import User

stripe.api_key = settings.STRIPE_SECRET_KEY


class BillingServiceError(Exception):
    pass


class BillingService:
    async def apply_coupon(self, db: AsyncSession, code: str, amount: Decimal) -> tuple[Decimal, Coupon | None]:
        result = await db.execute(select(Coupon).where(Coupon.code == code, Coupon.is_active == True))
        coupon = result.scalar_one_or_none()
        if coupon is None:
            raise BillingServiceError("invalid_coupon")
        if coupon.used_count >= coupon.max_uses:
            raise BillingServiceError("coupon_exhausted")
        if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
            raise BillingServiceError("coupon_expired")
        discount = amount * (Decimal(coupon.discount_percent) / Decimal(100))
        return amount - discount, coupon

    async def create_invoice(
        self, db: AsyncSession, user: User, plan_id: uuid.UUID,
        provider: PaymentProvider, coupon_code: str | None = None,
    ) -> Invoice:
        result = await db.execute(select(Plan).where(Plan.id == plan_id))
        plan = result.scalar_one_or_none()
        if plan is None:
            raise BillingServiceError("plan_not_found")

        amount = Decimal(str(plan.price_monthly))
        coupon = None
        if coupon_code:
            amount, coupon = await self.apply_coupon(db, coupon_code, amount)

        invoice = Invoice(
            user_id=user.id,
            plan_id=plan.id,
            provider=provider,
            amount=amount,
            coupon_code=coupon_code,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )

        if provider == PaymentProvider.STRIPE:
            intent = stripe.PaymentIntent.create(amount=int(amount * 100), currency="usd", metadata={"invoice_user": str(user.id)})
            invoice.external_reference = intent.id
        elif provider == PaymentProvider.PAYPAL:
            invoice.external_reference = await self._create_paypal_order(amount)
        elif provider == PaymentProvider.USDT_TRC20:
            invoice.crypto_address = settings.USDT_TRC20_ADDRESS
        elif provider == PaymentProvider.USDT_BEP20:
            invoice.crypto_address = settings.USDT_BEP20_ADDRESS

        db.add(invoice)
        if coupon:
            coupon.used_count += 1
        await db.commit()
        return invoice

    async def _create_paypal_order(self, amount: Decimal) -> str:
        base_url = "https://api-m.paypal.com" if settings.PAYPAL_MODE == "live" else "https://api-m.sandbox.paypal.com"
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                f"{base_url}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
            )
            auth_response.raise_for_status()
            access_token = auth_response.json()["access_token"]

            order_response = await client.post(
                f"{base_url}/v2/checkout/orders",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"intent": "CAPTURE", "purchase_units": [{"amount": {"currency_code": "USD", "value": str(amount)}}]},
            )
            order_response.raise_for_status()
            return order_response.json()["id"]

    async def confirm_payment(self, db: AsyncSession, invoice: Invoice) -> Subscription:
        invoice.status = PaymentStatus.PAID
        invoice.paid_at = datetime.now(timezone.utc)

        subscription = Subscription(
            user_id=invoice.user_id,
            plan_id=invoice.plan_id,
            status=SubscriptionStatus.ACTIVE,
            ends_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.add(subscription)

        user_result = await db.execute(select(User).where(User.id == invoice.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.plan_id = invoice.plan_id

        await db.commit()
        return subscription

    async def verify_crypto_payment(self, invoice: Invoice, tx_hash: str) -> bool:
        if invoice.provider == PaymentProvider.USDT_TRC20:
            return await self._verify_trc20(invoice, tx_hash)
        if invoice.provider == PaymentProvider.USDT_BEP20:
            return await self._verify_bep20(invoice, tx_hash)
        return False

    async def _verify_trc20(self, invoice: Invoice, tx_hash: str) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.trongrid.io/v1/transactions/{tx_hash}",
                headers={"TRON-PRO-API-KEY": settings.TRONGRID_API_KEY},
            )
            if response.status_code != 200:
                return False
            data = response.json()
            return bool(data.get("ret", [{}])[0].get("contractRet") == "SUCCESS")

    async def _verify_bep20(self, invoice: Invoice, tx_hash: str) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.bscscan.com/api",
                params={"module": "transaction", "action": "gettxreceiptstatus", "txhash": tx_hash, "apikey": settings.BSCSCAN_API_KEY},
            )
            if response.status_code != 200:
                return False
            data = response.json()
            return data.get("result", {}).get("status") == "1"


billing_service = BillingService()
