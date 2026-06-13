"""Наполнение базы данных тестовыми данными.

Запуск:
    python -m scripts.seed            # добавить данные (если БД пуста)
    python -m scripts.seed --reset    # пересоздать таблицы и заполнить заново

Создаёт набор категорий, операций за последние месяцы и месячные бюджеты,
чтобы можно было сразу посмотреть аналитику и интерфейс.
"""

from __future__ import annotations

import argparse
import random
from datetime import date

from app.database import Base, SessionLocal, engine, init_db
from app.models.budget import Budget
from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction

INCOME_CATEGORIES = ["Зарплата", "Фриланс", "Подарки", "Проценты по вкладу"]
EXPENSE_CATEGORIES = [
    "Продукты",
    "Транспорт",
    "Жильё",
    "Развлечения",
    "Здоровье",
    "Образование",
    "Кафе и рестораны",
]


def _reset_database() -> None:
    """Полностью пересоздаёт схему БД."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _months_back(n: int) -> list[tuple[int, int]]:
    """Возвращает список (год, месяц) за последние n месяцев включая текущий."""
    today = date.today()
    result: list[tuple[int, int]] = []
    year, month = today.year, today.month
    for _ in range(n):
        result.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(result))


def seed(reset: bool = False) -> None:
    if reset:
        _reset_database()
    else:
        init_db()

    rng = random.Random(42)  # фиксируем seed для воспроизводимости
    db = SessionLocal()
    try:
        if db.query(Category).count() > 0 and not reset:
            print("В базе уже есть данные — пропускаю заполнение. "
                  "Используйте --reset для пересоздания.")
            return

        # 1) Категории
        income_cats = [
            Category(name=name, type=TransactionType.INCOME)
            for name in INCOME_CATEGORIES
        ]
        expense_cats = [
            Category(name=name, type=TransactionType.EXPENSE)
            for name in EXPENSE_CATEGORIES
        ]
        db.add_all(income_cats + expense_cats)
        db.commit()
        for c in income_cats + expense_cats:
            db.refresh(c)

        # 2) Операции за последние 6 месяцев
        periods = _months_back(6)
        tx_count = 0
        for year, month in periods:
            # Доходы: 1–2 операции в месяц
            for _ in range(rng.randint(1, 2)):
                cat = rng.choice(income_cats)
                amount = round(rng.uniform(40_000, 120_000), 2)
                day = rng.randint(1, 28)
                db.add(Transaction(
                    amount=amount,
                    type=TransactionType.INCOME,
                    category_id=cat.id,
                    description=f"{cat.name} за {month:02d}.{year}",
                    occurred_on=date(year, month, day),
                ))
                tx_count += 1
            # Расходы: 8–15 операций в месяц
            for _ in range(rng.randint(8, 15)):
                cat = rng.choice(expense_cats)
                amount = round(rng.uniform(300, 15_000), 2)
                day = rng.randint(1, 28)
                db.add(Transaction(
                    amount=amount,
                    type=TransactionType.EXPENSE,
                    category_id=cat.id,
                    description=f"{cat.name}",
                    occurred_on=date(year, month, day),
                ))
                tx_count += 1
        db.commit()

        # 3) Бюджеты на текущий месяц для нескольких категорий расходов
        cur_year, cur_month = periods[-1]
        budget_targets = {
            "Продукты": 30_000,
            "Транспорт": 8_000,
            "Развлечения": 10_000,
            "Кафе и рестораны": 12_000,
        }
        by_name = {c.name: c for c in expense_cats}
        for name, limit in budget_targets.items():
            cat = by_name[name]
            db.add(Budget(
                category_id=cat.id,
                year=cur_year,
                month=cur_month,
                limit_amount=float(limit),
            ))
        db.commit()

        print("Готово. Добавлено:")
        print(f"  категорий: {len(income_cats) + len(expense_cats)}")
        print(f"  операций:  {tx_count}")
        print(f"  бюджетов:  {len(budget_targets)} (на {cur_month:02d}.{cur_year})")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Наполнение БД тестовыми данными")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="пересоздать таблицы перед заполнением",
    )
    args = parser.parse_args()
    seed(reset=args.reset)


if __name__ == "__main__":
    main()
