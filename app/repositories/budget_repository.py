"""Репозиторий бюджетов."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.budget import Budget


class BudgetRepository:
    """Доступ к данным бюджетов."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self, *, year: int | None = None, month: int | None = None) -> list[Budget]:
        stmt = select(Budget).order_by(Budget.year.desc(), Budget.month.desc())
        if year is not None:
            stmt = stmt.where(Budget.year == year)
        if month is not None:
            stmt = stmt.where(Budget.month == month)
        return list(self._db.scalars(stmt))

    def get(self, budget_id: int) -> Budget | None:
        return self._db.get(Budget, budget_id)

    def get_for_period(
        self, category_id: int, year: int, month: int
    ) -> Budget | None:
        stmt = select(Budget).where(
            Budget.category_id == category_id,
            Budget.year == year,
            Budget.month == month,
        )
        return self._db.scalars(stmt).first()

    def add(self, budget: Budget) -> Budget:
        self._db.add(budget)
        self._db.commit()
        self._db.refresh(budget)
        return budget

    def save(self, budget: Budget) -> Budget:
        self._db.commit()
        self._db.refresh(budget)
        return budget

    def delete(self, budget: Budget) -> None:
        self._db.delete(budget)
        self._db.commit()
