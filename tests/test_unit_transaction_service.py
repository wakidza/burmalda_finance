"""Модульные тесты TransactionService."""

from __future__ import annotations

from datetime import date

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.models.enums import TransactionType
from app.repositories import CategoryRepository, TransactionRepository
from app.schemas.category import CategoryCreate
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services import CategoryService, TransactionService


@pytest.fixture()
def categories(db) -> CategoryService:
    return CategoryService(CategoryRepository(db))


@pytest.fixture()
def service(db) -> TransactionService:
    return TransactionService(TransactionRepository(db), CategoryRepository(db))


@pytest.fixture()
def expense_cat(categories: CategoryService):
    return categories.create_category(
        CategoryCreate(name="Продукты", type=TransactionType.EXPENSE)
    )


@pytest.fixture()
def income_cat(categories: CategoryService):
    return categories.create_category(
        CategoryCreate(name="Зарплата", type=TransactionType.INCOME)
    )


def test_create_transaction(service: TransactionService, expense_cat) -> None:
    tx = service.create_transaction(
        TransactionCreate(
            amount=1500.5,
            type=TransactionType.EXPENSE,
            category_id=expense_cat.id,
            description="Магазин",
            occurred_on=date(2026, 1, 10),
        )
    )
    assert tx.id is not None
    assert tx.amount == 1500.5
    assert tx.occurred_on == date(2026, 1, 10)


def test_create_defaults_date_to_today(service: TransactionService, expense_cat) -> None:
    tx = service.create_transaction(
        TransactionCreate(
            amount=100, type=TransactionType.EXPENSE, category_id=expense_cat.id
        )
    )
    assert tx.occurred_on == date.today()


def test_type_mismatch_raises_validation(
    service: TransactionService, expense_cat
) -> None:
    # Тип операции income, а категория — расходная → ошибка.
    with pytest.raises(ValidationError):
        service.create_transaction(
            TransactionCreate(
                amount=100,
                type=TransactionType.INCOME,
                category_id=expense_cat.id,
            )
        )


def test_unknown_category_raises_not_found(service: TransactionService) -> None:
    with pytest.raises(NotFoundError):
        service.create_transaction(
            TransactionCreate(amount=100, type=TransactionType.EXPENSE, category_id=12345)
        )


def test_update_transaction_amount(service: TransactionService, expense_cat) -> None:
    tx = service.create_transaction(
        TransactionCreate(amount=100, type=TransactionType.EXPENSE, category_id=expense_cat.id)
    )
    updated = service.update_transaction(tx.id, TransactionUpdate(amount=250.75))
    assert updated.amount == 250.75


def test_update_changing_type_revalidates_category(
    service: TransactionService, expense_cat, income_cat
) -> None:
    tx = service.create_transaction(
        TransactionCreate(amount=100, type=TransactionType.EXPENSE, category_id=expense_cat.id)
    )
    # Меняем тип на income, но категория осталась расходной → ошибка.
    with pytest.raises(ValidationError):
        service.update_transaction(tx.id, TransactionUpdate(type=TransactionType.INCOME))
    # А смена типа вместе с подходящей категорией — успешна.
    ok = service.update_transaction(
        tx.id,
        TransactionUpdate(type=TransactionType.INCOME, category_id=income_cat.id),
    )
    assert ok.type == TransactionType.INCOME
    assert ok.category_id == income_cat.id


def test_delete_transaction(service: TransactionService, expense_cat) -> None:
    tx = service.create_transaction(
        TransactionCreate(amount=100, type=TransactionType.EXPENSE, category_id=expense_cat.id)
    )
    service.delete_transaction(tx.id)
    with pytest.raises(NotFoundError):
        service.get_transaction(tx.id)


def test_list_filters_by_type(service: TransactionService, expense_cat, income_cat) -> None:
    service.create_transaction(
        TransactionCreate(amount=10, type=TransactionType.EXPENSE, category_id=expense_cat.id)
    )
    service.create_transaction(
        TransactionCreate(amount=20, type=TransactionType.INCOME, category_id=income_cat.id)
    )
    expenses = service.list_transactions(type_=TransactionType.EXPENSE)
    assert len(expenses) == 1
    assert expenses[0].type == TransactionType.EXPENSE
