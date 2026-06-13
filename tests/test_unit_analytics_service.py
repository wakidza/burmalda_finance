"""Модульные тесты AnalyticsService (сводки, разбивки, тренды)."""

from __future__ import annotations

from datetime import date

import pytest

from app.models.enums import TransactionType
from app.repositories import CategoryRepository, TransactionRepository
from app.schemas.category import CategoryCreate
from app.schemas.transaction import TransactionCreate
from app.services import AnalyticsService, CategoryService, TransactionService


@pytest.fixture()
def categories(db) -> CategoryService:
    return CategoryService(CategoryRepository(db))


@pytest.fixture()
def transactions(db) -> TransactionService:
    return TransactionService(TransactionRepository(db), CategoryRepository(db))


@pytest.fixture()
def analytics(db) -> AnalyticsService:
    return AnalyticsService(TransactionRepository(db), CategoryRepository(db))


@pytest.fixture()
def setup_data(categories: CategoryService, transactions: TransactionService):
    salary = categories.create_category(
        CategoryCreate(name="Зарплата", type=TransactionType.INCOME)
    )
    food = categories.create_category(
        CategoryCreate(name="Продукты", type=TransactionType.EXPENSE)
    )
    transport = categories.create_category(
        CategoryCreate(name="Транспорт", type=TransactionType.EXPENSE)
    )
    transactions.create_transaction(
        TransactionCreate(amount=100_000, type=TransactionType.INCOME,
                          category_id=salary.id, occurred_on=date(2026, 2, 1))
    )
    transactions.create_transaction(
        TransactionCreate(amount=20_000, type=TransactionType.EXPENSE,
                          category_id=food.id, occurred_on=date(2026, 2, 10))
    )
    transactions.create_transaction(
        TransactionCreate(amount=5_000, type=TransactionType.EXPENSE,
                          category_id=transport.id, occurred_on=date(2026, 2, 12))
    )
    # Операция в другом месяце — не должна попасть в сводку февраля.
    transactions.create_transaction(
        TransactionCreate(amount=3_000, type=TransactionType.EXPENSE,
                          category_id=food.id, occurred_on=date(2026, 3, 1))
    )
    return {"food": food, "transport": transport, "salary": salary}


def test_monthly_summary(analytics: AnalyticsService, setup_data) -> None:
    summary = analytics.period_summary(year=2026, month=2)
    assert summary.total_income == 100_000
    assert summary.total_expense == 25_000
    assert summary.balance == 75_000


def test_yearly_summary_aggregates_all_months(
    analytics: AnalyticsService, setup_data
) -> None:
    summary = analytics.period_summary(year=2026)
    assert summary.total_expense == 28_000  # 25000 (фев) + 3000 (март)
    assert summary.month is None


def test_breakdown_by_category(analytics: AnalyticsService, setup_data) -> None:
    items = analytics.breakdown_by_category(
        type_=TransactionType.EXPENSE, year=2026, month=2
    )
    totals = {i.category_name: i.total for i in items}
    assert totals["Продукты"] == 20_000
    assert totals["Транспорт"] == 5_000
    # Отсортировано по убыванию суммы.
    assert items[0].total >= items[-1].total


def test_monthly_trend_has_twelve_points(
    analytics: AnalyticsService, setup_data
) -> None:
    trend = analytics.monthly_trend(year=2026)
    assert len(trend) == 12
    february = next(p for p in trend if p.month == 2)
    assert february.total_income == 100_000
    assert february.total_expense == 25_000
    march = next(p for p in trend if p.month == 3)
    assert march.total_expense == 3_000
