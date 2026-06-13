"""Модульные тесты CategoryService (бизнес-логика категорий)."""

from __future__ import annotations

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import TransactionType
from app.repositories import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services import CategoryService


@pytest.fixture()
def service(db) -> CategoryService:
    return CategoryService(CategoryRepository(db))


def test_create_category(service: CategoryService) -> None:
    cat = service.create_category(
        CategoryCreate(name="Продукты", type=TransactionType.EXPENSE)
    )
    assert cat.id is not None
    assert cat.name == "Продукты"
    assert cat.type == TransactionType.EXPENSE


def test_create_duplicate_raises_conflict(service: CategoryService) -> None:
    service.create_category(CategoryCreate(name="Зарплата", type=TransactionType.INCOME))
    with pytest.raises(ConflictError):
        service.create_category(
            CategoryCreate(name="Зарплата", type=TransactionType.INCOME)
        )


def test_same_name_different_type_is_allowed(service: CategoryService) -> None:
    a = service.create_category(CategoryCreate(name="Прочее", type=TransactionType.INCOME))
    b = service.create_category(CategoryCreate(name="Прочее", type=TransactionType.EXPENSE))
    assert a.id != b.id


def test_get_missing_raises_not_found(service: CategoryService) -> None:
    with pytest.raises(NotFoundError):
        service.get_category(999)


def test_update_category_name(service: CategoryService) -> None:
    cat = service.create_category(CategoryCreate(name="Еда", type=TransactionType.EXPENSE))
    updated = service.update_category(cat.id, CategoryUpdate(name="Питание"))
    assert updated.name == "Питание"


def test_update_to_existing_name_conflicts(service: CategoryService) -> None:
    service.create_category(CategoryCreate(name="Транспорт", type=TransactionType.EXPENSE))
    other = service.create_category(CategoryCreate(name="Такси", type=TransactionType.EXPENSE))
    with pytest.raises(ConflictError):
        service.update_category(other.id, CategoryUpdate(name="Транспорт"))


def test_delete_category(service: CategoryService) -> None:
    cat = service.create_category(CategoryCreate(name="Хобби", type=TransactionType.EXPENSE))
    service.delete_category(cat.id)
    with pytest.raises(NotFoundError):
        service.get_category(cat.id)
