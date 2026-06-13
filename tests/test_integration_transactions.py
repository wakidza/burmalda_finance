"""Интеграционные тесты HTTP-API операций."""

from __future__ import annotations

import pytest


@pytest.fixture()
def expense_category(client) -> int:
    res = client.post("/api/categories", json={"name": "Продукты", "type": "expense"})
    return res.json()["id"]


@pytest.fixture()
def income_category(client) -> int:
    res = client.post("/api/categories", json={"name": "Зарплата", "type": "income"})
    return res.json()["id"]


def test_create_transaction(client, expense_category) -> None:
    res = client.post(
        "/api/transactions",
        json={
            "amount": 1500.5,
            "type": "expense",
            "category_id": expense_category,
            "description": "Магазин у дома",
            "occurred_on": "2026-01-15",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["amount"] == 1500.5
    assert body["occurred_on"] == "2026-01-15"


def test_negative_amount_returns_422(client, expense_category) -> None:
    res = client.post(
        "/api/transactions",
        json={"amount": -10, "type": "expense", "category_id": expense_category},
    )
    assert res.status_code == 422


def test_type_mismatch_returns_422(client, expense_category) -> None:
    # income-операция в expense-категорию → бизнес-ошибка валидации.
    res = client.post(
        "/api/transactions",
        json={"amount": 100, "type": "income", "category_id": expense_category},
    )
    assert res.status_code == 422
    assert res.json()["error"]["type"] == "ValidationError"


def test_unknown_category_returns_404(client) -> None:
    res = client.post(
        "/api/transactions",
        json={"amount": 100, "type": "expense", "category_id": 4242},
    )
    assert res.status_code == 404


def test_list_and_filter_transactions(client, expense_category, income_category) -> None:
    client.post("/api/transactions", json={
        "amount": 100, "type": "expense", "category_id": expense_category,
        "occurred_on": "2026-02-01"})
    client.post("/api/transactions", json={
        "amount": 50_000, "type": "income", "category_id": income_category,
        "occurred_on": "2026-02-02"})

    all_tx = client.get("/api/transactions", params={"year": 2026, "month": 2}).json()
    assert len(all_tx) == 2

    only_income = client.get(
        "/api/transactions", params={"year": 2026, "month": 2, "type": "income"}
    ).json()
    assert len(only_income) == 1
    assert only_income[0]["type"] == "income"


def test_update_and_delete_transaction(client, expense_category) -> None:
    created = client.post("/api/transactions", json={
        "amount": 100, "type": "expense", "category_id": expense_category,
        "occurred_on": "2026-02-01"}).json()
    tx_id = created["id"]

    patched = client.patch(f"/api/transactions/{tx_id}", json={"amount": 333.33})
    assert patched.status_code == 200
    assert patched.json()["amount"] == 333.33

    assert client.delete(f"/api/transactions/{tx_id}").status_code == 204
    assert client.get(f"/api/transactions/{tx_id}").status_code == 404
