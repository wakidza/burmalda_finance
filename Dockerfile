# Многоступенчатость не нужна — приложение лёгкое. Базируемся на slim-образе.
FROM python:3.12-slim

# Не писать .pyc, выводить логи без буферизации.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Сначала зависимости — кешируется отдельным слоем.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Затем исходный код.
COPY app ./app
COPY static ./static
COPY scripts ./scripts

EXPOSE 8000

# Запуск ASGI-сервера. Хост 0.0.0.0 — чтобы был доступен снаружи контейнера.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
