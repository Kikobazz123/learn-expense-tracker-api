import pytest

from tests.conftest import auth_headers_for


def test_create_expense(client, auth_headers):
    r = client.post(
        "/expenses",
        json={"title": "Lunch", "amount": 12.5, "category": "Food"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert (body["title"], body["amount"], body["category"]) == ("Lunch", 12.5, "Food")
    assert body["id"] and body["owner_id"]
    assert body["created_at"] and body["updated_at"]


def test_create_rejects_unknown_category(client, auth_headers):
    r = client.post(
        "/expenses",
        json={"title": "Lunch", "amount": 1, "category": "Snacks"},
        headers=auth_headers,
    )
    assert r.status_code == 422


@pytest.mark.xfail(strict=True, reason="bug: duplicate ExpenseCreate drops validation")
@pytest.mark.parametrize("amount", [0, -5])
def test_create_rejects_non_positive_amount(client, auth_headers, amount):
    r = client.post(
        "/expenses",
        json={"title": "Refund", "amount": amount, "category": "Other"},
        headers=auth_headers,
    )
    assert r.status_code == 422


@pytest.mark.xfail(strict=True, reason="bug: duplicate ExpenseCreate drops validation")
def test_create_rejects_one_character_title(client, auth_headers):
    r = client.post(
        "/expenses",
        json={"title": "x", "amount": 1, "category": "Other"},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_list_returns_own_expenses(client, auth_headers, make_expense):
    make_expense("Lunch")
    make_expense("Bus", 2, "Transport")
    r = client.get("/expenses", headers=auth_headers)
    assert r.status_code == 200
    assert {e["title"] for e in r.json()} == {"Lunch", "Bus"}


def test_update_expense(client, auth_headers, make_expense):
    e = make_expense()
    r = client.put(
        f"/expenses/{e['id']}",
        json={"title": "Dinner", "amount": 30, "category": "Food"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert (r.json()["title"], r.json()["amount"]) == ("Dinner", 30)


def test_update_missing_expense_is_404(client, auth_headers):
    r = client.put(
        "/expenses/999",
        json={"title": "Dinner", "amount": 30, "category": "Food"},
        headers=auth_headers,
    )
    assert r.status_code == 404


def test_delete_expense(client, auth_headers, make_expense):
    e = make_expense()
    r = client.delete(f"/expenses/{e['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert client.get("/expenses", headers=auth_headers).json() == []
    assert client.delete(f"/expenses/{e['id']}", headers=auth_headers).status_code == 404


def test_users_cannot_see_or_change_each_others_expenses(client, make_expense):
    e = make_expense()
    bob = auth_headers_for(client, "bob", "bob@example.com")

    assert client.get("/expenses", headers=bob).json() == []
    payload = {"title": "Hijack", "amount": 1, "category": "Other"}
    assert client.put(f"/expenses/{e['id']}", json=payload, headers=bob).status_code == 404
    assert client.delete(f"/expenses/{e['id']}", headers=bob).status_code == 404
