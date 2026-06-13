"""Схемы финансовых операций."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TransactionType


class TransactionBase(BaseModel):
    amount: float = Field(
        ...,
        gt=0,
        le=1_000_000_000,
        description="Сумма операции, больше нуля",
        examples=[1500.50],
    )
    type: TransactionType = Field(..., description="Тип операции: income/expense")
    category_id: int = Field(..., gt=0, description="ID категории")
    description: str = Field(
        default="", max_length=255, description="Комментарий к операции"
    )
    occurred_on: date | None = Field(
        default=None,
        description="Дата операции (YYYY-MM-DD). По умолчанию — сегодня.",
    )

    @field_validator("amount")
    @classmethod
    def _round_amount(cls, value: float) -> float:
        # Деньги храним с точностью до копеек.
        return round(float(value), 2)

    @field_validator("description")
    @classmethod
    def _strip_description(cls, value: str) -> str:
        return value.strip()


class TransactionCreate(TransactionBase):
    """Данные для создания операции."""


class TransactionUpdate(BaseModel):
    """Частичное обновление операции (любое подмножество полей)."""

    amount: float | None = Field(default=None, gt=0, le=1_000_000_000)
    type: TransactionType | None = None
    category_id: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=255)
    occurred_on: date | None = None

    @field_validator("amount")
    @classmethod
    def _round_amount(cls, value: float | None) -> float | None:
        return None if value is None else round(float(value), 2)


class TransactionRead(BaseModel):
    """Операция, возвращаемая клиенту."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    type: TransactionType
    category_id: int
    description: str
    occurred_on: date
    created_at: datetime
