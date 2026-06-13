# Инструкция по развёртыванию и запуску

Документ описывает запуск «Бурмалда Finance» локально, в Docker и на облачных
платформах, а также настройку CI/CD.

---

## 1. Переменные окружения

| Переменная | По умолчанию | Назначение |
|------------|--------------|-----------|
| `DATABASE_URL` | `sqlite:///./finance.db` | Строка подключения к БД |
| `CORS_ORIGINS` | `*` | Разрешённые источники (через запятую) |
| `DEBUG` | `false` | Подробные логи SQL и ошибок |

Для продакшена рекомендуется задать конкретные `CORS_ORIGINS` и при нагрузке —
PostgreSQL: `DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db`.

---

## 2. Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m scripts.seed --reset       # тестовые данные (опционально)
uvicorn app.main:app --reload        # http://127.0.0.1:8000
```

Для запуска на другом порту: `uvicorn app.main:app --port 8080`.

---

## 3. Запуск в Docker

```bash
# Сборка образа
docker build -t burmalda-finance .

# Запуск (данные в контейнере эфемерны)
docker run -p 8000:8000 burmalda-finance

# Запуск с сохранением БД на хосте (том)
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:////data/finance.db \
  -v "$(pwd)/data:/data" \
  burmalda-finance
```

### docker-compose (опционально)

```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=sqlite:////data/finance.db
      - CORS_ORIGINS=*
    volumes:
      - ./data:/data
```

Запуск: `docker compose up --build`.

---

## 4. Развёртывание на облачных платформах

Приложение — стандартное ASGI‑приложение, команда запуска одинакова:
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

### Railway / Render

1. Подключить репозиторий.
2. Build command: `pip install -r requirements.txt`.
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. (Опционально) переменные `DATABASE_URL`, `CORS_ORIGINS`.

> Файловая система этих платформ часто эфемерна — для постоянного хранения
> подключите управляемую БД PostgreSQL и задайте `DATABASE_URL`.

### Heroku

`Procfile`:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Vercel

Подходит для статического фронтенда + Python‑функций; для монолитного ASGI
приложения проще использовать Railway/Render. При необходимости фронтенд
(`static/`) можно вынести на Vercel, а API развернуть отдельно.

---

## 5. CI/CD

Файл [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) на каждый push и
pull request:

1. устанавливает Python (3.11 и 3.12);
2. ставит зависимости;
3. прогоняет тесты (`pytest`);
4. выполняет smoke‑проверку (импорт приложения и сидирование БД).

Для непрерывного развёртывания (CD) можно добавить job, который после успешных
тестов собирает Docker‑образ и публикует/деплоит его (например, через
`railwayapp/cli` или `docker push` в реестр).

---

## 6. Проверка после развёртывания

```bash
curl https://<ваш-домен>/api/health
# {"status":"ok","app":"Бурмалда Finance","version":"1.0.0"}
```

Открыть `https://<ваш-домен>/` (интерфейс) и `https://<ваш-домен>/docs` (Swagger).

---

## 7. Резервное копирование (SQLite)

БД — один файл (`finance.db`). Резервная копия — копирование файла при
остановленном приложении или командой SQLite:

```bash
sqlite3 finance.db ".backup backup.db"
```
