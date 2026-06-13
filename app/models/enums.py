"""Перечисления предметной области."""

from __future__ import annotations

import enum


class TransactionType(str, enum.Enum):
    """Тип операции/категории: доход или расход."""

    INCOME = "income"
    EXPENSE = "expense"

    def __str__(self) -> str:  # удобный вывод в логах и сообщениях
        return self.value
