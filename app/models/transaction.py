"""ORM-модель финансовой операции (доход или расход)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import TransactionType

if TYPE_CHECKING:
    from app.models.category import Category


class Transaction(Base):
    """Денежная операция, привязанная к категории."""

    __tablename__ = "transactions"
    __table_args__ = (
        # Индекс ускоряет выборки за период и аналитику по дате.
        Index("ix_transactions_date_type", "occurred_on", "type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False, length=20),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    category: Mapped["Category"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Transaction id={self.id} amount={self.amount} "
            f"type={self.type} date={self.occurred_on}>"
        )
