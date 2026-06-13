"""Схемы бюджетов (месячных лимитов расходов)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BudgetBase(BaseModel):
    category_id: int = Field(..., gt=0, description="ID категории расходов")
    year: int = Field(..., ge=2000, le=2100, description="Год бюджета")
    month: int = Field(..., ge=1, le=12, description="Месяц бюджета (1..12)")
    limit_amount: float = Field(
        ..., gt=0, le=1_000_000_000, description="Лимит расходов на месяц"
    )

    @field_validator("limit_amount")
    @classmethod
    def _round_limit(cls, value: float) -> float:
        return round(float(value), 2)


class BudgetCreate(BudgetBase):
    """Данные для создания бюджета."""


class BudgetUpdate(BaseModel):
    """Изменение лимита существующего бюджета."""

    limit_amount: float = Field(..., gt=0, le=1_000_000_000)

    @field_validator("limit_amount")
    @classmethod
    def _round_limit(cls, value: float) -> float:
        return round(float(value), 2)


class BudgetRead(BudgetBase):
    """Бюджет, возвращаемый клиенту."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class BudgetStatus(BaseModel):
    """Состояние исполнения бюджета за период."""

    budget_id: int
    category_id: int
    category_name: str
    year: int
    month: int
    limit_amount: float
    spent: float
    remaining: float
    used_percent: float = Field(description="Процент использования лимита")
    over_budget: bool = Field(description="Лимит превышен?")
