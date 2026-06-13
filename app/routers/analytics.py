"""Маршруты аналитики."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.dependencies import AnalyticsServiceDep
from app.models.enums import TransactionType
from app.schemas.analytics import (
    CategoryBreakdownItem,
    MonthlyPoint,
    PeriodSummary,
)

router = APIRouter(prefix="/api/analytics", tags=["Аналитика"])


@router.get("/summary", response_model=PeriodSummary, summary="Сводка за период")
def summary(
    service: AnalyticsServiceDep,
    year: int = Query(..., ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
) -> PeriodSummary:
    """Доходы, расходы и баланс за год или конкретный месяц."""
    return service.period_summary(year=year, month=month)


@router.get(
    "/by-category",
    response_model=list[CategoryBreakdownItem],
    summary="Разбивка по категориям",
)
def by_category(
    service: AnalyticsServiceDep,
    type: TransactionType = Query(..., description="income или expense"),
    year: int = Query(..., ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
) -> list[CategoryBreakdownItem]:
    return service.breakdown_by_category(type_=type, year=year, month=month)


@router.get(
    "/monthly",
    response_model=list[MonthlyPoint],
    summary="Тренд по месяцам года",
)
def monthly(
    service: AnalyticsServiceDep,
    year: int = Query(..., ge=2000, le=2100),
) -> list[MonthlyPoint]:
    """Доходы и расходы по каждому из 12 месяцев года."""
    return service.monthly_trend(year=year)
