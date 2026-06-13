"""Репозиторий категорий."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import TransactionType


class CategoryRepository:
    """Доступ к данным категорий."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self, type_: TransactionType | None = None) -> list[Category]:
        stmt = select(Category).order_by(Category.type, Category.name)
        if type_ is not None:
            stmt = stmt.where(Category.type == type_)
        return list(self._db.scalars(stmt))

    def get(self, category_id: int) -> Category | None:
        return self._db.get(Category, category_id)

    def get_by_name_and_type(
        self, name: str, type_: TransactionType
    ) -> Category | None:
        stmt = select(Category).where(
            Category.name == name, Category.type == type_
        )
        return self._db.scalars(stmt).first()

    def add(self, category: Category) -> Category:
        self._db.add(category)
        self._db.commit()
        self._db.refresh(category)
        return category

    def save(self, category: Category) -> Category:
        self._db.commit()
        self._db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self._db.delete(category)
        self._db.commit()
