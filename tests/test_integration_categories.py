"""Интеграционные тесты HTTP-API категорий."""

from __future__ import annotations


def test_health(client) -> None:
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_create_and_list_category(client) -> None:
    res = client.post("/api/categories", json={"name": "Продукты", "type": "expense"})
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Продукты"
    assert body["type"] == "expense"
    assert "id" in body

    res = client.get("/api/categories")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_filter_categories_by_type(client) -> None:
    client.post("/api/categories", json={"name": "Зарплата", "type": "income"})
    client.post("/api/categories", json={"name": "Кафе", "type": "expense"})
    res = client.get("/api/categories", params={"type": "income"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["type"] == "income"


def test_duplicate_category_returns_409(client) -> None:
    client.post("/api/categories", json={"name": "Авто", "type": "expense"})
    res = client.post("/api/categories", json={"name": "Авто", "type": "expense"})
    assert res.status_code == 409
    assert res.json()["error"]["type"] == "ConflictError"


def test_get_missing_category_returns_404(client) -> None:
    res = client.get("/api/categories/999")
    assert res.status_code == 404
    assert res.json()["error"]["type"] == "NotFoundError"


def test_update_category(client) -> None:
    created = client.post("/api/categories", json={"name": "Еда", "type": "expense"}).json()
    res = client.patch(f"/api/categories/{created['id']}", json={"name": "Питание"})
    assert res.status_code == 200
    assert res.json()["name"] == "Питание"


def test_delete_category(client) -> None:
    created = client.post("/api/categories", json={"name": "Хобби", "type": "expense"}).json()
    res = client.delete(f"/api/categories/{created['id']}")
    assert res.status_code == 204
    assert client.get(f"/api/categories/{created['id']}").status_code == 404


def test_invalid_category_payload_returns_422(client) -> None:
    # Пустое имя нарушает min_length.
    res = client.post("/api/categories", json={"name": "", "type": "expense"})
    assert res.status_code == 422
