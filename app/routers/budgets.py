"""Маршруты управления бюджетами."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies import BudgetServiceDep
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetStatus, BudgetUpdate

router = APIRouter(prefix="/api/budgets", tags=["Бюджеты"])


@router.get("", response_model=list[BudgetRead], summary="Список бюджетов")
def list_budgets(
    service: BudgetServiceDep,
    year: int | None = Query(default=None, ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
) -> list[BudgetRead]:
    return service.list_budgets(year=year, month=month)


@router.get(
    "/status",
    response_model=list[BudgetStatus],
    summary="Исполнение бюджетов за период",
)
def budgets_status(
    service: BudgetServiceDep,
    year: int = Query(..., ge=2000, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
) -> list[BudgetStatus]:
    """Сколько потрачено относительно лимита по каждому бюджету."""
    return service.get_status(year=year, month=month)


@router.post(
    "",
    response_model=BudgetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать бюджет",
)
def create_budget(payload: BudgetCreate, service: BudgetServiceDep) -> BudgetRead:
    return service.create_budget(payload)


@router.patch(
    "/{budget_id}", response_model=BudgetRead, summary="Изменить лимит бюджета"
)
def update_budget(
    budget_id: int, payload: BudgetUpdate, service: BudgetServiceDep
) -> BudgetRead:
    return service.update_budget(budget_id, payload)


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить бюджет",
)
def delete_budget(budget_id: int, service: BudgetServiceDep) -> None:
    service.delete_budget(budget_id)
