"""Бизнес-логика аналитики: сводки, разбивки и тренды."""

from __future__ import annotations

from app.models.enums import TransactionType
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.analytics import (
    CategoryBreakdownItem,
    MonthlyPoint,
    PeriodSummary,
)


class AnalyticsService:
    """Расчёт агрегированных показателей по операциям."""

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        category_repository: CategoryRepository,
    ) -> None:
        self._transactions = transaction_repository
        self._categories = category_repository

    def period_summary(
        self, *, year: int, month: int | None = None
    ) -> PeriodSummary:
        income = self._transactions.total_amount(
            TransactionType.INCOME, year=year, month=month
        )
        expense = self._transactions.total_amount(
            TransactionType.EXPENSE, year=year, month=month
        )
        income = round(income, 2)
        expense = round(expense, 2)
        return PeriodSummary(
            year=year,
            month=month,
            total_income=income,
            total_expense=expense,
            balance=round(income - expense, 2),
        )

    def breakdown_by_category(
        self, *, type_: TransactionType, year: int, month: int | None = None
    ) -> list[CategoryBreakdownItem]:
        rows = self._transactions.sum_by_category(type_, year=year, month=month)
        # Подтягиваем названия категорий одним проходом.
        names = {c.id: c.name for c in self._categories.list()}
        return [
            CategoryBreakdownItem(
                category_id=cid,
                category_name=names.get(cid, f"#{cid}"),
                total=round(total, 2),
            )
            for cid, total in rows
        ]

    def monthly_trend(self, *, year: int) -> list[MonthlyPoint]:
        totals = self._transactions.monthly_totals(year)
        return [
            MonthlyPoint(
                month=month,
                total_income=round(totals[month]["income"], 2),
                total_expense=round(totals[month]["expense"], 2),
            )
            for month in range(1, 13)
        ]
