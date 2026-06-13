"""Слой бизнес-логики (services).

Каждый сервис реализует правила предметной области и зависит только от
репозиториев (через конструктор) — это упрощает модульное тестирование
с подменой репозиториев и соответствует принципам SOLID.
"""

from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService
from app.services.budget_service import BudgetService
from app.services.analytics_service import AnalyticsService

__all__ = [
    "CategoryService",
    "TransactionService",
    "BudgetService",
    "AnalyticsService",
]
