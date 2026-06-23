import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.db.models import Outbox
from tests.test_utils import create_payment_payload

@pytest.mark.asyncio
async def test_outbox_record_created(client: AsyncClient, db_session):
    headers = {"X-API-Key": "secret-api-key-123", "Idempotency-Key": "outbox-test"}
    payload = create_payment_payload(amount=100, currency="RUB")
    await client.post("/api/v1/payments/", json=payload, headers=headers)

    result = await db_session.execute(select(Outbox).where(Outbox.event_type == "payment.created"))
    outbox = result.scalar_one()
    assert outbox.status == "pending"
    assert outbox.payload["payment_id"] is not None