# Справочник REST API

Базовый URL: `/api`. Формат — JSON. Интерактивная документация и «живые»
запросы доступны в **Swagger UI** по адресу `/docs`, схема — `/openapi.json`.

Единый формат ошибки:

```json
{ "error": { "type": "NotFoundError", "message": "Категория с id=5 не найдена" } }
```

| Код | Когда |
|-----|-------|
| 200 | Успешный GET/PATCH |
| 201 | Создан ресурс (POST) |
| 204 | Успешное удаление (DELETE), тело пустое |
| 404 | Ресурс не найден (`NotFoundError`) |
| 409 | Конфликт уникальности (`ConflictError`) |
| 422 | Ошибка валидации (Pydantic или бизнес‑правило) |

---

## Категории — `/api/categories`

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/categories?type=income\|expense` | Список категорий (фильтр по типу опционален) |
| POST | `/api/categories` | Создать категорию |
| GET | `/api/categories/{id}` | Получить категорию |
| PATCH | `/api/categories/{id}` | Изменить название |
| DELETE | `/api/categories/{id}` | Удалить (каскадно удаляет операции и бюджеты) |

**Тело POST:**
```json
{ "name": "Продукты", "type": "expense" }
```

---

## Операции — `/api/transactions`

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/transactions` | Список с фильтрами: `type`, `category_id`, `year`, `month`, `limit`, `offset` |
| POST | `/api/transactions` | Создать операцию |
| GET | `/api/transactions/{id}` | Получить операцию |
| PATCH | `/api/transactions/{id}` | Частично изменить |
| DELETE | `/api/transactions/{id}` | Удалить |

**Тело POST:**
```json
{
  "amount": 1500.50,
  "type": "expense",
  "category_id": 1,
  "description": "Магазин у дома",
  "occurred_on": "2026-06-13"
}
```
`occurred_on` можно не указывать — подставится текущая дата.
Бизнес‑правило: `type` операции должен совпадать с типом категории.

---

## Бюджеты — `/api/budgets`

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/budgets?year=&month=` | Список бюджетов |
| GET | `/api/budgets/status?year=&month=` | Исполнение бюджетов за период |
| POST | `/api/budgets` | Создать бюджет (только для категории расходов) |
| PATCH | `/api/budgets/{id}` | Изменить лимит |
| DELETE | `/api/budgets/{id}` | Удалить |

**Тело POST:**
```json
{ "category_id": 1, "year": 2026, "month": 6, "limit_amount": 30000 }
```

**Ответ `/status`:**
```json
[
  {
    "budget_id": 2, "category_id": 6, "category_name": "Транспорт",
    "year": 2026, "month": 6, "limit_amount": 8000.0,
    "spent": 15597.73, "remaining": -7597.73,
    "used_percent": 195.0, "over_budget": true
  }
]
```

---

## Аналитика — `/api/analytics`

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/analytics/summary?year=&month=` | Сводка: доходы, расходы, баланс |
| GET | `/api/analytics/by-category?type=&year=&month=` | Разбивка по категориям |
| GET | `/api/analytics/monthly?year=` | Тренд по 12 месяцам года |

`month` опционален: без него агрегаты считаются за весь год.

**Пример `summary`:**
```json
{ "year": 2026, "month": 6, "total_income": 40575.27,
  "total_expense": 42286.21, "balance": -1710.94 }
```

---

## Служебные

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/health` | Проверка живости сервиса |
| GET | `/` | Веб‑интерфейс (статический фронтенд) |
| GET | `/docs`, `/redoc` | Документация API |

---

## Примеры запросов (curl)

```bash
# Создать категорию
curl -X POST http://127.0.0.1:8000/api/categories \
  -H "Content-Type: application/json" \
  -d '{"name":"Продукты","type":"expense"}'

# Добавить расход
curl -X POST http://127.0.0.1:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"amount":1500.50,"type":"expense","category_id":1,"occurred_on":"2026-06-13"}'

# Сводка за июнь 2026
curl "http://127.0.0.1:8000/api/analytics/summary?year=2026&month=6"

# Исполнение бюджетов
curl "http://127.0.0.1:8000/api/budgets/status?year=2026&month=6"
```
