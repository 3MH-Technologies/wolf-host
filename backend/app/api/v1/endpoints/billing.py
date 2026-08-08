import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.plan import Plan
from app.models.payment import Invoice, PaymentStatus
from app.schemas.billing import PlanResponse, CreateInvoiceRequest, InvoiceResponse
from app.core.dependencies import get_current_user
from app.services.billing_service import billing_service, BillingServiceError

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.is_active == True))
    return result.scalars().all()


@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(payload: CreateInvoiceRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        invoice = await billing_service.create_invoice(db, user, payload.plan_id, payload.provider, payload.coupon_code)
    except BillingServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return invoice


@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.user_id == user.id).order_by(Invoice.created_at.desc()))
    return result.scalars().all()


@router.post("/invoices/{invoice_id}/confirm-crypto")
async def confirm_crypto_payment(invoice_id: uuid.UUID, tx_hash: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invoice_not_found")
    if invoice.status != PaymentStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invoice_not_pending")

    verified = await billing_service.verify_crypto_payment(invoice, tx_hash)
    if not verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="transaction_not_verified")

    invoice.crypto_tx_hash = tx_hash
    await billing_service.confirm_payment(db, invoice)
    return {"message": "payment_confirmed"}


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    import stripe
    from app.core.config import settings

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_signature")

    if event["type"] == "payment_intent.succeeded":
        intent_id = event["data"]["object"]["id"]
        result = await db.execute(select(Invoice).where(Invoice.external_reference == intent_id))
        invoice = result.scalar_one_or_none()
        if invoice and invoice.status == PaymentStatus.PENDING:
            await billing_service.confirm_payment(db, invoice)

    return {"received": True}
