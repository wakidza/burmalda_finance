"""Модульные тесты BudgetService, включая расчёт исполнения бюджета."""

from __future__ import annotations

from datetime import date

import pytest

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enums import TransactionType
from app.repositories import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from app.schemas.budget import BudgetCreate
from app.schemas.category import CategoryCreate
from app.schemas.transaction import TransactionCreate
from app.services import BudgetService, CategoryService, TransactionService


@pytest.fixture()
def categories(db) -> CategoryService:
    return CategoryService(CategoryRepository(db))


@pytest.fixture()
def transactions(db) -> TransactionService:
    return TransactionService(TransactionRepository(db), CategoryRepository(db))


@pytest.fixture()
def service(db) -> BudgetService:
    return BudgetService(
        BudgetRepository(db), CategoryRepository(db), TransactionRepository(db)
    )


def test_budget_only_for_expense_category(
    service: BudgetService, categories: CategoryService
) -> None:
    income = categories.create_category(
        CategoryCreate(name="Зарплата", type=TransactionType.INCOME)
    )
    with pytest.raises(ValidationError):
        service.create_budget(
            BudgetCreate(category_id=income.id, year=2026, month=1, limit_amount=1000)
        )


def test_budget_unknown_category(service: BudgetService) -> None:
    with pytest.raises(NotFoundError):
        service.create_budget(
            BudgetCreate(category_id=999, year=2026, month=1, limit_amount=1000)
        )


def test_duplicate_budget_conflicts(
    service: BudgetService, categories: CategoryService
) -> None:
    cat = categories.create_category(
        CategoryCreate(name="Продукты", type=TransactionType.EXPENSE)
    )
    service.create_budget(
        BudgetCreate(category_id=cat.id, year=2026, month=1, limit_amount=5000)
    )
    with pytest.raises(ConflictError):
        service.create_budget(
            BudgetCreate(category_id=cat.id, year=2026, month=1, limit_amount=6000)
        )


def test_status_computes_spent_and_over_budget(
    service: BudgetService,
    categories: CategoryService,
    transactions: TransactionService,
) -> None:
    cat = categories.create_category(
        CategoryCreate(name="Продукты", type=TransactionType.EXPENSE)
    )
    service.create_budget(
        BudgetCreate(category_id=cat.id, year=2026, month=3, limit_amount=10_000)
    )
    # Тратим 12 000 → перерасход.
    for amount in (5000, 4000, 3000):
        transactions.create_transaction(
            TransactionCreate(
                amount=amount,
                type=TransactionType.EXPENSE,
                category_id=cat.id,
                occurred_on=date(2026, 3, 15),
            )
        )
    statuses = service.get_status(year=2026, month=3)
    assert len(statuses) == 1
    st = statuses[0]
    assert st.spent == 12_000
    assert st.limit_amount == 10_000
    assert st.remaining == -2000
    assert st.over_budget is True
    assert st.used_percent == 120.0


def test_status_within_budget(
    service: BudgetService,
    categories: CategoryService,
    transactions: TransactionService,
) -> None:
    cat = categories.create_category(
        CategoryCreate(name="Транспорт", type=TransactionType.EXPENSE)
    )
    service.create_budget(
        BudgetCreate(category_id=cat.id, year=2026, month=3, limit_amount=8000)
    )
    transactions.create_transaction(
        TransactionCreate(
            amount=2000,
            type=TransactionType.EXPENSE,
            category_id=cat.id,
            occurred_on=date(2026, 3, 5),
        )
    )
    st = service.get_status(year=2026, month=3)[0]
    assert st.spent == 2000
    assert st.remaining == 6000
    assert st.over_budget is False
    assert st.used_percent == 25.0
