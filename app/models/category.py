"""ORM-модель категории доходов/расходов."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import TransactionType

if TYPE_CHECKING:  # только для подсказок типов, без циклических импортов в рантайме
    from app.models.budget import Budget
    from app.models.transaction import Transaction


class Category(Base):
    """Категория (например, «Зарплата», «Продукты», «Транспорт»)."""

    __tablename__ = "categories"
    # Имя категории уникально в пределах своего типа (доход/расход).
    __table_args__ = (
        UniqueConstraint("name", "type", name="uq_category_name_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False, length=20),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - вспомогательный вывод
        return f"<Category id={self.id} name={self.name!r} type={self.type}>"
