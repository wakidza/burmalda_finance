"""Схемы категорий."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TransactionType


class CategoryBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Название категории",
        examples=["Продукты"],
    )
    type: TransactionType = Field(
        ..., description="Тип категории: income (доход) или expense (расход)"
    )

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Название категории не может быть пустым")
        return cleaned


class CategoryCreate(CategoryBase):
    """Данные для создания категории."""


class CategoryUpdate(BaseModel):
    """Данные для частичного обновления категории."""

    name: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Название категории не может быть пустым")
        return cleaned


class CategoryRead(CategoryBase):
    """Категория, возвращаемая клиенту."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
