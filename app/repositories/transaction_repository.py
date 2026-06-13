"""Репозиторий финансовых операций."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import TransactionType
from app.models.transaction import Transaction


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    """Возвращает первую дату месяца и первую дату следующего месяца."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


class TransactionRepository:
    """Доступ к данным операций и агрегаты для аналитики."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ---- CRUD ----------------------------------------------------------

    def list(
        self,
        *,
        type_: TransactionType | None = None,
        category_id: int | None = None,
        year: int | None = None,
        month: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        stmt = select(Transaction).order_by(
            Transaction.occurred_on.desc(), Transaction.id.desc()
        )
        if type_ is not None:
            stmt = stmt.where(Transaction.type == type_)
        if category_id is not None:
            stmt = stmt.where(Transaction.category_id == category_id)
        if year is not None and month is not None:
            start, end = _month_bounds(year, month)
            stmt = stmt.where(
                Transaction.occurred_on >= start, Transaction.occurred_on < end
            )
        elif year is not None:
            stmt = stmt.where(
                Transaction.occurred_on >= date(year, 1, 1),
                Transaction.occurred_on < date(year + 1, 1, 1),
            )
        stmt = stmt.limit(limit).offset(offset)
        return list(self._db.scalars(stmt))

    def get(self, transaction_id: int) -> Transaction | None:
        return self._db.get(Transaction, transaction_id)

    def add(self, transaction: Transaction) -> Transaction:
        self._db.add(transaction)
        self._db.commit()
        self._db.refresh(transaction)
        return transaction

    def save(self, transaction: Transaction) -> Transaction:
        self._db.commit()
        self._db.refresh(transaction)
        return transaction

    def delete(self, transaction: Transaction) -> None:
        self._db.delete(transaction)
        self._db.commit()

    # ---- Агрегаты для аналитики ---------------------------------------

    def total_amount(
        self,
        type_: TransactionType,
        *,
        year: int,
        month: int | None = None,
        category_id: int | None = None,
    ) -> float:
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
            Transaction.type == type_
        )
        if month is not None:
            start, end = _month_bounds(year, month)
        else:
            start, end = date(year, 1, 1), date(year + 1, 1, 1)
        stmt = stmt.where(
            Transaction.occurred_on >= start, Transaction.occurred_on < end
        )
        if category_id is not None:
            stmt = stmt.where(Transaction.category_id == category_id)
        return float(self._db.scalar(stmt) or 0.0)

    def sum_by_category(
        self,
        type_: TransactionType,
        *,
        year: int,
        month: int | None = None,
    ) -> list[tuple[int, float]]:
        """Сумма операций по каждой категории за период."""
        stmt = select(
            Transaction.category_id,
            func.coalesce(func.sum(Transaction.amount), 0.0),
        ).where(Transaction.type == type_)
        if month is not None:
            start, end = _month_bounds(year, month)
        else:
            start, end = date(year, 1, 1), date(year + 1, 1, 1)
        stmt = (
            stmt.where(
                Transaction.occurred_on >= start, Transaction.occurred_on < end
            )
            .group_by(Transaction.category_id)
            .order_by(func.sum(Transaction.amount).desc())
        )
        return [(int(cid), float(total)) for cid, total in self._db.execute(stmt)]

    def monthly_totals(self, year: int) -> dict[int, dict[str, float]]:
        """Доходы и расходы по каждому месяцу года.

        Возвращает {месяц: {"income": x, "expense": y}}.
        """
        # strftime("%m", ...) извлекает месяц из даты (SQLite).
        month_expr = func.strftime("%m", Transaction.occurred_on)
        stmt = (
            select(
                month_expr,
                Transaction.type,
                func.coalesce(func.sum(Transaction.amount), 0.0),
            )
            .where(
                Transaction.occurred_on >= date(year, 1, 1),
                Transaction.occurred_on < date(year + 1, 1, 1),
            )
            .group_by(month_expr, Transaction.type)
        )

        result: dict[int, dict[str, float]] = {
            m: {"income": 0.0, "expense": 0.0} for m in range(1, 13)
        }
        for month_str, type_value, total in self._db.execute(stmt):
            month = int(month_str)
            key = type_value.value if hasattr(type_value, "value") else str(type_value)
            result[month][key] = float(total)
        return result

    def count_by_category(self, category_id: int) -> int:
        stmt = select(func.count()).where(Transaction.category_id == category_id)
        return int(self._db.scalar(stmt) or 0)
