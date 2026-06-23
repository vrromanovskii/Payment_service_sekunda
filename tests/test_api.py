import pytest
from httpx import AsyncClient
from tests.test_utils import create_payment_payload

@pytest.mark.asyncio
async def test_create_payment_success(client: AsyncClient):
    headers = {"X-API-Key": "secret-api-key-123", "Idempotency-Key": "test-key-1"}
    payload = create_payment_payload(amount=100.50, currency="USD")
    resp = await client.post("/api/v1/payments/", json=payload, headers=headers)
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert "payment_id" in data

@pytest.mark.asyncio
async def test_create_payment_idempotency(client: AsyncClient):
    headers = {"X-API-Key": "secret-api-key-123", "Idempotency-Key": "test-key-2"}
    payload = create_payment_payload(amount=50.0, currency="EUR")
    resp1 = await client.post("/api/v1/payments/", json=payload, headers=headers)
    resp2 = await client.post("/api/v1/payments/", json=payload, headers=headers)
    assert resp1.status_code == 202
    assert resp2.status_code == 202
    assert resp1.json()["payment_id"] == resp2.json()["payment_id"]

@pytest.mark.asyncio
async def test_get_payment(client: AsyncClient):
    headers = {"X-API-Key": "secret-api-key-123", "Idempotency-Key": "test-key-3"}
    payload = create_payment_payload(amount=200, currency="RUB")
    create_resp = await client.post("/api/v1/payments/", json=payload, headers=headers)
    payment_id = create_resp.json()["payment_id"]
    resp = await client.get(f"/api/v1/payments/{payment_id}", headers={"X-API-Key": "secret-api-key-123"})
    assert resp.status_code == 200
    assert resp.json()["amount"] == "200.00"