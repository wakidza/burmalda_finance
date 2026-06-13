"""Преобразование доменных исключений в HTTP-ответы.

Единый формат ошибки для клиента:
    {"error": {"type": "...", "message": "..."}}
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)

# Сопоставление типа исключения и HTTP-кода.
# 422 задаём литералом: имя константы менялось между версиями Starlette.
_STATUS_MAP: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    ValidationError: 422,  # Unprocessable Content
}


def _error_body(exc: DomainError) -> dict:
    return {"error": {"type": exc.__class__.__name__, "message": exc.message}}


def register_error_handlers(app: FastAPI) -> None:
    """Регистрирует обработчики доменных исключений в приложении."""

    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        http_status = _STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=http_status, content=_error_body(exc))
