# Архитектура и UML‑диаграммы

Документ описывает архитектуру приложения «Бурмалда Finance» и содержит
диаграммы в нотации UML (Mermaid — отображаются на GitHub/GitLab).

---

## 1. Слоистая архитектура

```mermaid
flowchart TD
    UI["Веб-интерфейс<br/>(static: HTML/CSS/JS)"]
    subgraph Backend["FastAPI приложение"]
        R["routers/<br/>HTTP-слой"]
        S["services/<br/>Бизнес-логика"]
        Repo["repositories/<br/>Доступ к данным"]
        M["models/<br/>ORM-модели"]
        Sch["schemas/<br/>Pydantic DTO + валидация"]
        Core["core/<br/>Исключения и обработчики"]
        Dep["dependencies.py<br/>Сборка DI"]
    end
    DB[("SQLite<br/>finance.db")]

    UI -->|"HTTP/JSON (fetch)"| R
    R -->|Depends| Dep
    Dep --> S
    S --> Repo
    Repo --> M
    M --> DB
    R -.валидация.-> Sch
    S -.бросает.-> Core
    Core -.->|HTTP-коды| R
```

**Принцип:** запрос проходит сверху вниз. Каждый слой зависит только от
соседнего нижнего и общается через абстракции (репозитории, схемы). Это
реализует принципы **SRP** (одна ответственность на слой) и **DIP**
(сервисы зависят от репозиториев, внедряемых через конструктор).

---

## 2. Диаграмма вариантов использования (Use Case)

```mermaid
flowchart LR
    User(("Пользователь"))
    Dev(("Интегратор/<br/>разработчик"))

    subgraph System["Бурмалда Finance"]
        UC1["Управлять категориями"]
        UC2["Вести операции<br/>(добавить/изменить/удалить)"]
        UC3["Фильтровать операции<br/>по периоду и типу"]
        UC4["Задавать бюджеты"]
        UC5["Контролировать исполнение<br/>бюджета"]
        UC6["Смотреть аналитику<br/>(сводка, разбивка, тренд)"]
        UC7["Обращаться к REST API<br/>(Swagger/OpenAPI)"]
    end

    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    Dev --> UC7

    UC2 -. include .-> UC1
    UC4 -. include .-> UC1
    UC5 -. include .-> UC4
```

---

## 3. Диаграмма классов (Class Diagram)

Показаны ключевые классы серверной части и их связи.

```mermaid
classDiagram
    direction LR

    class TransactionType {
        <<enumeration>>
        INCOME
        EXPENSE
    }

    class Category {
        +int id
        +str name
        +TransactionType type
        +datetime created_at
    }
    class Transaction {
        +int id
        +float amount
        +TransactionType type
        +str description
        +date occurred_on
        +int category_id
    }
    class Budget {
        +int id
        +int category_id
        +int year
        +int month
        +float limit_amount
    }

    Category "1" --> "0..*" Transaction : содержит
    Category "1" --> "0..*" Budget : ограничивает

    class CategoryRepository {
        +list(type) Category[]
        +get(id) Category
        +get_by_name_and_type(name, type) Category
        +add(category) Category
        +save(category) Category
        +delete(category) void
    }
    class TransactionRepository {
        +list(filters) Transaction[]
        +get(id) Transaction
        +add(tx) Transaction
        +total_amount(...) float
        +sum_by_category(...) list
        +monthly_totals(year) dict
    }
    class BudgetRepository {
        +list(year, month) Budget[]
        +get_for_period(cat, y, m) Budget
        +add(budget) Budget
    }

    class CategoryService {
        +create_category(dto) Category
        +update_category(id, dto) Category
        +delete_category(id) void
    }
    class TransactionService {
        +create_transaction(dto) Transaction
        +update_transaction(id, dto) Transaction
        -_validate_category(id, type) void
    }
    class BudgetService {
        +create_budget(dto) Budget
        +get_status(year, month) BudgetStatus[]
    }
    class AnalyticsService {
        +period_summary(year, month) PeriodSummary
        +breakdown_by_category(...) list
        +monthly_trend(year) MonthlyPoint[]
    }

    CategoryService --> CategoryRepository
    TransactionService --> TransactionRepository
    TransactionService --> CategoryRepository
    BudgetService --> BudgetRepository
    BudgetService --> CategoryRepository
    BudgetService --> TransactionRepository
    AnalyticsService --> TransactionRepository
    AnalyticsService --> CategoryRepository

    CategoryRepository ..> Category
    TransactionRepository ..> Transaction
    BudgetRepository ..> Budget
```

**Замечания по SOLID:**
- сервисы получают репозитории через конструктор (внедрение зависимостей);
- сервис не знает, как именно репозиторий хранит данные (SQLite/PostgreSQL);
- каждый репозиторий работает только со своей сущностью.

---

## 4. Диаграмма последовательности (Sequence) — создание операции

Сценарий: пользователь добавляет расход через интерфейс.

```mermaid
sequenceDiagram
    actor U as Пользователь
    participant FE as Фронтенд (app.js)
    participant API as Router (transactions)
    participant SVC as TransactionService
    participant CR as CategoryRepository
    participant TR as TransactionRepository
    participant DB as SQLite

    U->>FE: Заполняет форму и нажимает «Добавить»
    FE->>API: POST /api/transactions {amount, type, category_id, date}
    API->>API: Валидация Pydantic (amount>0, поля)
    API->>SVC: create_transaction(dto)
    SVC->>CR: get(category_id)
    CR->>DB: SELECT * FROM categories WHERE id=?
    DB-->>CR: Category | None
    CR-->>SVC: Category
    alt Категория не найдена
        SVC-->>API: NotFoundError
        API-->>FE: 404 {error}
    else Тип операции ≠ тип категории
        SVC-->>API: ValidationError
        API-->>FE: 422 {error}
    else Всё корректно
        SVC->>TR: add(transaction)
        TR->>DB: INSERT INTO transactions ...
        DB-->>TR: id
        TR-->>SVC: Transaction
        SVC-->>API: Transaction
        API-->>FE: 201 {transaction}
        FE->>FE: Обновляет сводку, список, бюджеты
        FE-->>U: Тост «Операция добавлена»
    end
```

---

## 5. Диаграмма последовательности — расчёт исполнения бюджета

```mermaid
sequenceDiagram
    actor U as Пользователь
    participant FE as Фронтенд
    participant API as Router (budgets)
    participant SVC as BudgetService
    participant BR as BudgetRepository
    participant TR as TransactionRepository

    U->>FE: Выбирает месяц
    FE->>API: GET /api/budgets/status?year&month
    API->>SVC: get_status(year, month)
    SVC->>BR: list(year, month)
    BR-->>SVC: Budget[]
    loop по каждому бюджету
        SVC->>TR: total_amount(EXPENSE, year, month, category_id)
        TR-->>SVC: spent
        SVC->>SVC: remaining, used_percent, over_budget
    end
    SVC-->>API: BudgetStatus[]
    API-->>FE: 200 [...]
    FE-->>U: Индикаторы исполнения (зелёный/жёлтый/красный)
```

---

## 6. Обработка ошибок

Бизнес‑логика бросает доменные исключения (`NotFoundError`, `ConflictError`,
`ValidationError`), не зная про HTTP. Обработчик в `core/error_handlers.py`
переводит их в коды ответа и единый формат:

```json
{ "error": { "type": "ValidationError", "message": "…" } }
```

| Исключение | HTTP‑код |
|------------|----------|
| `NotFoundError` | 404 Not Found |
| `ConflictError` | 409 Conflict |
| `ValidationError` (бизнес‑правило) | 422 Unprocessable |
| Ошибка валидации Pydantic | 422 (стандартный формат FastAPI) |
