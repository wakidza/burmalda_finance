"""Бизнес-логика работы с категориями."""

from __future__ import annotations

from app.core.exceptions import ConflictError, NotFoundError
from app.models.category import Category
from app.models.enums import TransactionType
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Правила создания/изменения/удаления категорий."""

    def __init__(self, repository: CategoryRepository) -> None:
        self._repo = repository

    def list_categories(self, type_: TransactionType | None = None) -> list[Category]:
        return self._repo.list(type_)

    def get_category(self, category_id: int) -> Category:
        category = self._repo.get(category_id)
        if category is None:
            raise NotFoundError(f"Категория с id={category_id} не найдена")
        return category

    def create_category(self, data: CategoryCreate) -> Category:
        # Бизнес-правило: имя категории уникально в пределах типа.
        existing = self._repo.get_by_name_and_type(data.name, data.type)
        if existing is not None:
            raise ConflictError(
                f"Категория «{data.name}» с типом «{data.type}» уже существует"
            )
        category = Category(name=data.name, type=data.type)
        return self._repo.add(category)

    def update_category(self, category_id: int, data: CategoryUpdate) -> Category:
        category = self.get_category(category_id)
        if data.name is not None and data.name != category.name:
            clash = self._repo.get_by_name_and_type(data.name, category.type)
            if clash is not None and clash.id != category.id:
                raise ConflictError(
                    f"Категория «{data.name}» с типом «{category.type}» уже существует"
                )
            category.name = data.name
        return self._repo.save(category)

    def delete_category(self, category_id: int) -> None:
        category = self.get_category(category_id)
        # Связанные операции и бюджеты удаляются каскадно (cascade в модели).
        self._repo.delete(category)
