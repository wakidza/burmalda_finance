"""Поставщики зависимостей (Dependency Injection) для FastAPI.

Здесь собирается цепочка «сессия БД → репозитории → сервисы».
Маршруты (routers) запрашивают готовый сервис через ``Depends`` и не знают,
как именно он сконструирован. Это инверсия управления (IoC) — упрощает
тестирование и замену реализаций.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from app.services import (
    AnalyticsService,
    BudgetService,
    CategoryService,
    TransactionService,
)

DbSession = Annotated[Session, Depends(get_db)]


# ---- Репозитории -------------------------------------------------------

def get_category_repository(db: DbSession) -> CategoryRepository:
    return CategoryRepository(db)


def get_transaction_repository(db: DbSession) -> TransactionRepository:
    return TransactionRepository(db)


def get_budget_repository(db: DbSession) -> BudgetRepository:
    return BudgetRepository(db)


CategoryRepo = Annotated[CategoryRepository, Depends(get_category_repository)]
TransactionRepo = Annotated[
    TransactionRepository, Depends(get_transaction_repository)
]
BudgetRepo = Annotated[BudgetRepository, Depends(get_budget_repository)]


# ---- Сервисы -----------------------------------------------------------

def get_category_service(repo: CategoryRepo) -> CategoryService:
    return CategoryService(repo)


def get_transaction_service(
    transactions: TransactionRepo, categories: CategoryRepo
) -> TransactionService:
    return TransactionService(transactions, categories)


def get_budget_service(
    budgets: BudgetRepo,
    categories: CategoryRepo,
    transactions: TransactionRepo,
) -> BudgetService:
    return BudgetService(budgets, categories, transactions)


def get_analytics_service(
    transactions: TransactionRepo, categories: CategoryRepo
) -> AnalyticsService:
    return AnalyticsService(transactions, categories)


CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
TransactionServiceDep = Annotated[
    TransactionService, Depends(get_transaction_service)
]
BudgetServiceDep = Annotated[BudgetService, Depends(get_budget_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
