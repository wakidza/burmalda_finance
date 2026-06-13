"""Маршруты управления финансовыми операциями."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies import TransactionServiceDep
from app.models.enums import TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)

router = APIRouter(prefix="/api/transactions", tags=["Операции"])


@router.get("", response_model=list[TransactionRead], summary="Список операций")
def list_transactions(
    service: TransactionServiceDep,
    type: TransactionType | None = None,
    category_id: int | None = Query(default=None, gt=0),
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[TransactionRead]:
    """Возвращает операции с фильтрами по типу, категории и периоду."""
    return service.list_transactions(
        type_=type,
        category_id=category_id,
        year=year,
        month=month,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать операцию",
)
def create_transaction(
    payload: TransactionCreate, service: TransactionServiceDep
) -> TransactionRead:
    return service.create_transaction(payload)


@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Получить операцию",
)
def get_transaction(
    transaction_id: int, service: TransactionServiceDep
) -> TransactionRead:
    return service.get_transaction(transaction_id)


@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Изменить операцию",
)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    service: TransactionServiceDep,
) -> TransactionRead:
    return service.update_transaction(transaction_id, payload)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить операцию",
)
def delete_transaction(
    transaction_id: int, service: TransactionServiceDep
) -> None:
    service.delete_transaction(transaction_id)
