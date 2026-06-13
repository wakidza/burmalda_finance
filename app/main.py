"""Точка входа приложения: фабрика FastAPI.

Здесь собирается приложение: настройка CORS, подключение маршрутов,
обработчиков ошибок, статического фронтенда и инициализация БД.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.error_handlers import register_error_handlers
from app.database import init_db
from app.routers import analytics, budgets, categories, transactions

# Каталог со статическим фронтендом (HTML/CSS/JS).
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

API_DESCRIPTION = """
**Бурмалда Finance** — REST API сервиса учёта личных финансов.

Возможности:
* категории доходов и расходов;
* финансовые операции с фильтрами по периоду/типу/категории;
* месячные бюджеты и контроль их исполнения;
* аналитика: сводки, разбивки по категориям, тренды по месяцам.

Документация эндпоинтов доступна в форматах Swagger UI (`/docs`)
и ReDoc (`/redoc`).
"""


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Жизненный цикл приложения: на старте создаём таблицы БД."""
    # Для разработки/демо создаём схему автоматически; в проде — миграции.
    init_db()
    yield


def create_app() -> FastAPI:
    """Фабрика приложения (упрощает создание изолированных экземпляров в тестах)."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=API_DESCRIPTION,
        contact={"name": "Команда практики", "url": "https://example.com"},
        license_info={"name": "MIT"},
        lifespan=lifespan,
    )

    # CORS — чтобы фронтенд (в т. ч. с другого хоста) мог обращаться к API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Обработчики доменных исключений → корректные HTTP-коды.
    register_error_handlers(app)

    # Маршруты API.
    app.include_router(categories.router)
    app.include_router(transactions.router)
    app.include_router(budgets.router)
    app.include_router(analytics.router)

    @app.get("/api/health", tags=["Служебные"], summary="Проверка живости")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name, "version": settings.app_version}

    # Статический фронтенд: отдаём index.html на корне и файлы из /static.
    if STATIC_DIR.exists():
        app.mount(
            "/static", StaticFiles(directory=str(STATIC_DIR)), name="static"
        )

        @app.get("/", include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(str(STATIC_DIR / "index.html"))

    return app


app = create_app()
