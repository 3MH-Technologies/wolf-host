from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.models.payment import PaymentProvider, PaymentStatus
from app.models.plan import PlanTier


class PlanResponse(BaseModel):
    id: uuid.UUID
    tier: PlanTier
    name: str
    price_monthly: float
    max_bots: int
    max_containers: int
    cpu_limit: float
    ram_limit_mb: int
    storage_limit_mb: int
    bandwidth_limit_mb: int
    network_access: bool

    model_config = {"from_attributes": True}


class CreateInvoiceRequest(BaseModel):
    plan_id: uuid.UUID
    provider: PaymentProvider
    coupon_code: str | None = None


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    status: PaymentStatus
    amount: float
    currency: str
    provider: PaymentProvider
    crypto_address: str | None
    external_reference: str | None
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class ApplyCouponRequest(BaseModel):
    code: str = Field(min_length=3, max_length=64)
