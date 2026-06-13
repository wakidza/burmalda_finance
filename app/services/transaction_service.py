"""Бизнес-логика работы с финансовыми операциями."""

from __future__ import annotations

from datetime import date

from app.core.exceptions import NotFoundError, ValidationError
from app.models.transaction import Transaction
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    """Правила создания/изменения/удаления операций.

    Зависит от двух репозиториев: операций и категорий (для проверки
    существования и соответствия типа категории типу операции).
    """

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        category_repository: CategoryRepository,
    ) -> None:
        self._repo = transaction_repository
        self._categories = category_repository

    def _validate_category(self, category_id: int, type_) -> None:
        category = self._categories.get(category_id)
        if category is None:
            raise NotFoundError(f"Категория с id={category_id} не найдена")
        # Бизнес-правило: тип операции должен совпадать с типом категории.
        if category.type != type_:
            raise ValidationError(
                "Тип операции не совпадает с типом категории "
                f"(операция: {type_}, категория: {category.type})"
            )

    def list_transactions(
        self,
        *,
        type_=None,
        category_id: int | None = None,
        year: int | None = None,
        month: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        return self._repo.list(
            type_=type_,
            category_id=category_id,
            year=year,
            month=month,
            limit=limit,
            offset=offset,
        )

    def get_transaction(self, transaction_id: int) -> Transaction:
        transaction = self._repo.get(transaction_id)
        if transaction is None:
            raise NotFoundError(f"Операция с id={transaction_id} не найдена")
        return transaction

    def create_transaction(self, data: TransactionCreate) -> Transaction:
        self._validate_category(data.category_id, data.type)
        transaction = Transaction(
            amount=data.amount,
            type=data.type,
            category_id=data.category_id,
            description=data.description,
            occurred_on=data.occurred_on or date.today(),
        )
        return self._repo.add(transaction)

    def update_transaction(
        self, transaction_id: int, data: TransactionUpdate
    ) -> Transaction:
        transaction = self.get_transaction(transaction_id)

        new_type = data.type if data.type is not None else transaction.type
        new_category_id = (
            data.category_id
            if data.category_id is not None
            else transaction.category_id
        )
        # Если изменился тип или категория — повторно проверяем соответствие.
        if data.type is not None or data.category_id is not None:
            self._validate_category(new_category_id, new_type)

        if data.amount is not None:
            transaction.amount = data.amount
        if data.type is not None:
            transaction.type = data.type
        if data.category_id is not None:
            transaction.category_id = data.category_id
        if data.description is not None:
            transaction.description = data.description.strip()
        if data.occurred_on is not None:
            transaction.occurred_on = data.occurred_on

        return self._repo.save(transaction)

    def delete_transaction(self, transaction_id: int) -> None:
        transaction = self.get_transaction(transaction_id)
        self._repo.delete(transaction)
