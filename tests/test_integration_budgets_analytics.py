"""Интеграционные тесты HTTP-API бюджетов и аналитики."""

from __future__ import annotations

import pytest


@pytest.fixture()
def data(client):
    """Готовит категории и операции за февраль 2026."""
    food = client.post("/api/categories", json={"name": "Продукты", "type": "expense"}).json()
    salary = client.post("/api/categories", json={"name": "Зарплата", "type": "income"}).json()
    client.post("/api/transactions", json={
        "amount": 100_000, "type": "income", "category_id": salary["id"],
        "occurred_on": "2026-02-01"})
    client.post("/api/transactions", json={
        "amount": 12_000, "type": "expense", "category_id": food["id"],
        "occurred_on": "2026-02-10"})
    return {"food": food, "salary": salary}


def test_summary_endpoint(client, data) -> None:
    res = client.get("/api/analytics/summary", params={"year": 2026, "month": 2})
    assert res.status_code == 200
    body = res.json()
    assert body["total_income"] == 100_000
    assert body["total_expense"] == 12_000
    assert body["balance"] == 88_000


def test_breakdown_endpoint(client, data) -> None:
    res = client.get(
        "/api/analytics/by-category",
        params={"type": "expense", "year": 2026, "month": 2},
    )
    assert res.status_code == 200
    items = res.json()
    assert items[0]["category_name"] == "Продукты"
    assert items[0]["total"] == 12_000


def test_monthly_trend_endpoint(client, data) -> None:
    res = client.get("/api/analytics/monthly", params={"year": 2026})
    assert res.status_code == 200
    assert len(res.json()) == 12


def test_budget_lifecycle_and_status(client, data) -> None:
    food_id = data["food"]["id"]
    # Создаём бюджет 10 000 на февраль — при расходах 12 000 будет перерасход.
    created = client.post("/api/budgets", json={
        "category_id": food_id, "year": 2026, "month": 2, "limit_amount": 10_000})
    assert created.status_code == 201

    status = client.get("/api/budgets/status", params={"year": 2026, "month": 2}).json()
    assert len(status) == 1
    assert status[0]["spent"] == 12_000
    assert status[0]["over_budget"] is True

    # Поднимаем лимит — перерасход исчезает.
    budget_id = created.json()["id"]
    client.patch(f"/api/budgets/{budget_id}", json={"limit_amount": 20_000})
    status2 = client.get("/api/budgets/status", params={"year": 2026, "month": 2}).json()
    assert status2[0]["over_budget"] is False
    assert status2[0]["remaining"] == 8_000


def test_budget_for_income_category_rejected(client, data) -> None:
    salary_id = data["salary"]["id"]
    res = client.post("/api/budgets", json={
        "category_id": salary_id, "year": 2026, "month": 2, "limit_amount": 1000})
    assert res.status_code == 422
    assert res.json()["error"]["type"] == "ValidationError"


def test_root_serves_frontend(client) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "Бурмалда" in res.text
