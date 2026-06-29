# импорты из FastAPI
from fastapi import APIRouter, Depends, HTTPException, Header
# импортируем асинхронную сессию и функцию создания сессии БД
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
# импорт pydantic-схем
from app.schemas.payment import PaymentCreate, PaymentCreateResponse, PaymentResponse
# импорт функций бизнес-логики
from app.services.payment import create_payment, get_payment
# импорт зависимости для проверки API-ключа
from app.api.dependencies import verify_api_key
# импорт констант hhtp-статусов
from fastapi import status

# создаем экземпляр API-роутера
router = APIRouter(prefix="/api/v1/payments", tags=["payments"]) # tags=["payments"] — группирует эндпоинты в Swagger-документации под заголовком «payments»

@router.post("/", status_code=status.HTTP_202_ACCEPTED, response_model=PaymentCreateResponse) # Декоратор FastAPI, который связывает HTTP-метод POST с путём "/" относительно префикса роутера
async def create_payment_endpoint(
    payment: PaymentCreate,
    idempotency_key: str = Header(..., description="Уникальный ключ идемпотентности"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key) # надо, чтобы зависимость отработала
):
    """
    Создание платежа. Если ключ идемпотентности уже использован, возвращает существующий платеж.
    """
    created_payment = await create_payment(db, payment, idempotency_key)
    return PaymentCreateResponse(
        payment_id=created_payment.id,
        status=created_payment.status,
        created_at=created_payment.created_at
    ) # формируем ответ по схеме PaymentCreateResponse, используя данные из только что созданного или найденного платежа

@router.get("/{payment_id}", response_model=PaymentResponse) #Декоратор для GET-запроса с параметром пути {payment_id}
async def get_payment_endpoint(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    payment = await get_payment(db, payment_id) # вызываем функцию get_payment для поиска платежа по ID
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
    ) # если платеж найден, формируем ответ по схеме PaymentResponse, заполняя все поля данными из объекта payment