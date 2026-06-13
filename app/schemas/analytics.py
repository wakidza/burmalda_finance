"""Схемы аналитики (сводки и разбивки)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PeriodSummary(BaseModel):
    """Сводка за период: доходы, расходы и баланс."""

    year: int
    month: int | None = Field(
        default=None, description="Месяц (если сводка месячная), иначе null"
    )
    total_income: float
    total_expense: float
    balance: float


class CategoryBreakdownItem(BaseModel):
    """Сумма операций по одной категории."""

    category_id: int
    category_name: str
    total: float


class MonthlyPoint(BaseModel):
    """Точка для графика по месяцам года."""

    month: int = Field(..., ge=1, le=12)
    total_income: float
    total_expense: float
