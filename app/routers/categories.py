"""Маршруты управления категориями."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.dependencies import CategoryServiceDep
from app.models.enums import TransactionType
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/api/categories", tags=["Категории"])


@router.get("", response_model=list[CategoryRead], summary="Список категорий")
def list_categories(
    service: CategoryServiceDep,
    type: TransactionType | None = None,
) -> list[CategoryRead]:
    """Возвращает все категории, опционально фильтруя по типу."""
    return service.list_categories(type)


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать категорию",
)
def create_category(
    payload: CategoryCreate, service: CategoryServiceDep
) -> CategoryRead:
    return service.create_category(payload)


@router.get(
    "/{category_id}", response_model=CategoryRead, summary="Получить категорию"
)
def get_category(category_id: int, service: CategoryServiceDep) -> CategoryRead:
    return service.get_category(category_id)


@router.patch(
    "/{category_id}", response_model=CategoryRead, summary="Изменить категорию"
)
def update_category(
    category_id: int, payload: CategoryUpdate, service: CategoryServiceDep
) -> CategoryRead:
    return service.update_category(category_id, payload)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить категорию",
)
def delete_category(category_id: int, service: CategoryServiceDep) -> None:
    service.delete_category(category_id)
