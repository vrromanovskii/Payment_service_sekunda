# app/api/endpoints/payments.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.payment import PaymentCreate, PaymentCreateResponse, PaymentResponse
from app.services.payment import create_payment, get_payment
from app.api.dependencies import verify_api_key
from fastapi import status

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

@router.post("/", status_code=status.HTTP_202_ACCEPTED, response_model=PaymentCreateResponse)
async def create_payment_endpoint(
    payment: PaymentCreate,
    idempotency_key: str = Header(..., description="Уникальный ключ идемпотентности"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Создание платежа. Если ключ идемпотентности уже использован, возвращает существующий платеж.
    """
    created_payment = await create_payment(db, payment, idempotency_key)
    return PaymentCreateResponse(
        payment_id=created_payment.id,
        status=created_payment.status,
        created_at=created_payment.created_at
    )

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment_endpoint(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    payment = await get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse(
        id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        meta=payment.meta,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        updated_at=payment.updated_at
    )