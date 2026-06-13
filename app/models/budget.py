"""ORM-модель бюджета (месячный лимит расходов по категории)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.category import Category


class Budget(Base):
    """Лимит расходов по категории на конкретный месяц (год + месяц)."""

    __tablename__ = "budgets"
    __table_args__ = (
        # Один бюджет на категорию в пределах одного месяца.
        UniqueConstraint(
            "category_id", "year", "month", name="uq_budget_category_period"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..12
    limit_amount: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    category: Mapped["Category"] = relationship(back_populates="budgets")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Budget id={self.id} category_id={self.category_id} "
            f"{self.year}-{self.month:02d} limit={self.limit_amount}>"
        )
