"""Слой доступа к данным (Repository pattern).

Репозитории инкапсулируют все запросы к БД. Бизнес-логика (services)
работает с репозиториями, а не с SQLAlchemy напрямую — это упрощает
тестирование и замену источника данных (принцип DIP из SOLID).
"""

from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.budget_repository import BudgetRepository

__all__ = [
    "CategoryRepository",
    "TransactionRepository",
    "BudgetRepository",
]
