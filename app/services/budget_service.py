"""Бизнес-логика работы с бюджетами (месячными лимитами расходов)."""

from __future__ import annotations

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.budget import Budget
from app.models.enums import TransactionType
from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.budget import BudgetCreate, BudgetStatus, BudgetUpdate


class BudgetService:
    """Правила работы с бюджетами и расчёт их исполнения."""

    def __init__(
        self,
        budget_repository: BudgetRepository,
        category_repository: CategoryRepository,
        transaction_repository: TransactionRepository,
    ) -> None:
        self._repo = budget_repository
        self._categories = category_repository
        self._transactions = transaction_repository

    def list_budgets(
        self, *, year: int | None = None, month: int | None = None
    ) -> list[Budget]:
        return self._repo.list(year=year, month=month)

    def get_budget(self, budget_id: int) -> Budget:
        budget = self._repo.get(budget_id)
        if budget is None:
            raise NotFoundError(f"Бюджет с id={budget_id} не найден")
        return budget

    def create_budget(self, data: BudgetCreate) -> Budget:
        category = self._categories.get(data.category_id)
        if category is None:
            raise NotFoundError(f"Категория с id={data.category_id} не найдена")
        # Бюджет имеет смысл только для категорий расходов.
        if category.type != TransactionType.EXPENSE:
            raise ValidationError(
                "Бюджет можно задать только для категории расходов (expense)"
            )
        existing = self._repo.get_for_period(
            data.category_id, data.year, data.month
        )
        if existing is not None:
            raise ConflictError(
                "Бюджет для этой категории на указанный месяц уже существует"
            )
        budget = Budget(
            category_id=data.category_id,
            year=data.year,
            month=data.month,
            limit_amount=data.limit_amount,
        )
        return self._repo.add(budget)

    def update_budget(self, budget_id: int, data: BudgetUpdate) -> Budget:
        budget = self.get_budget(budget_id)
        budget.limit_amount = data.limit_amount
        return self._repo.save(budget)

    def delete_budget(self, budget_id: int) -> None:
        budget = self.get_budget(budget_id)
        self._repo.delete(budget)

    def get_status(
        self, *, year: int, month: int | None = None
    ) -> list[BudgetStatus]:
        """Считает исполнение бюджетов за период (по умолчанию — все месяцы года)."""
        budgets = self._repo.list(year=year, month=month)
        statuses: list[BudgetStatus] = []
        for budget in budgets:
            spent = self._transactions.total_amount(
                TransactionType.EXPENSE,
                year=budget.year,
                month=budget.month,
                category_id=budget.category_id,
            )
            spent = round(spent, 2)
            remaining = round(budget.limit_amount - spent, 2)
            used_percent = (
                round(spent / budget.limit_amount * 100, 1)
                if budget.limit_amount > 0
                else 0.0
            )
            statuses.append(
                BudgetStatus(
                    budget_id=budget.id,
                    category_id=budget.category_id,
                    category_name=budget.category.name,
                    year=budget.year,
                    month=budget.month,
                    limit_amount=budget.limit_amount,
                    spent=spent,
                    remaining=remaining,
                    used_percent=used_percent,
                    over_budget=spent > budget.limit_amount,
                )
            )
        return statuses
