"""Доменные исключения приложения.

Слой бизнес-логики не должен знать про HTTP. Поэтому сервисы бросают
доменные исключения, а HTTP-слой (обработчики в ``error_handlers``)
переводит их в корректные коды ответа. Это соблюдение принципа
разделения ответственности (SRP) и инверсии зависимостей (DIP).
"""

from __future__ import annotations


class DomainError(Exception):
    """Базовое доменное исключение."""

    message: str = "Доменная ошибка"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message


class NotFoundError(DomainError):
    """Запрашиваемая сущность не найдена."""

    message = "Объект не найден"


class ConflictError(DomainError):
    """Нарушение уникальности или конфликт состояния."""

    message = "Конфликт данных"


class ValidationError(DomainError):
    """Нарушение бизнес-правила валидации."""

    message = "Некорректные данные"
