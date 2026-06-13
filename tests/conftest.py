"""Общие фикстуры pytest.

Каждый тест работает с изолированной БД SQLite в памяти, чтобы тесты не
зависели друг от друга и не трогали реальный файл finance.db.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app


@pytest.fixture()
def engine():
    """Движок in-memory SQLite, общий для всех соединений теста."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # одно соединение → данные видны всем сессиям
    )
    Base.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(bind=eng)
        eng.dispose()


@pytest.fixture()
def session_factory(engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


@pytest.fixture()
def db(session_factory) -> Iterator[Session]:
    """Сессия БД для модульных тестов сервисов/репозиториев."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(session_factory) -> Iterator[TestClient]:
    """HTTP-клиент с подменённой зависимостью get_db на тестовую БД."""
    app = create_app()

    def _override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
