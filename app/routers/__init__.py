"""HTTP-слой: маршруты FastAPI."""

from app.routers import analytics, budgets, categories, transactions

__all__ = ["categories", "transactions", "budgets", "analytics"]
