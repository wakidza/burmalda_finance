"""Конфигурация приложения.

Настройки читаются из переменных окружения с разумными значениями по умолчанию.
Принцип KISS: один источник конфигурации, без лишних зависимостей.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Неизменяемый набор настроек приложения."""

    app_name: str = "Бурмалда Finance"
    app_version: str = "1.0.0"

    # Строка подключения к БД. По умолчанию — локальный файл SQLite.
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./finance.db")

    # Разрешённые источники для CORS (через запятую). "*" — любой источник.
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    # Режим отладки (подробные ошибки, авто-перезагрузка и т. п.).
    debug: bool = _bool_env("DEBUG", False)

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# Единый экземпляр настроек на всё приложение.
settings = Settings()
