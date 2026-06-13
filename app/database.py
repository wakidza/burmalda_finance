"""Настройка подключения к базе данных (SQLAlchemy 2.0).

Здесь создаётся engine, фабрика сессий и базовый класс моделей.
Функция ``get_db`` используется как FastAPI-зависимость и гарантирует
корректное закрытие сессии после обработки запроса.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Для SQLite требуется отключить проверку потока (FastAPI работает в нескольких).
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""


def get_db() -> Iterator[Session]:
    """FastAPI-зависимость: выдаёт сессию и закрывает её после запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создаёт таблицы по описанию моделей (если их ещё нет)."""
    # Импорт моделей нужен, чтобы они зарегистрировались в metadata.
    from app import models  # noqa: F401  (side-effect import)

    Base.metadata.create_all(bind=engine)
