from tests.conftest import auth_headers_for


def test_summary_when_empty(client, auth_headers):
    r = client.get("/summary", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"total_expenses": 0, "total_amount": 0, "average_expense": 0}


def test_summary_totals_and_rounded_average(client, auth_headers, make_expense):
    make_expense("Rent", 10, "Bills")
    make_expense("Food A", 20, "Food")
    make_expense("Food B", 5, "Food")
    r = client.get("/summary", headers=auth_headers).json()
    assert r == {"total_expenses": 3, "total_amount": 35, "average_expense": 11.67}


def test_category_summary(client, auth_headers, make_expense):
    make_expense("Rent", 10, "Bills")
    make_expense("Food A", 20, "Food")
    make_expense("Food B", 5, "Food")
    r = client.get("/summary/categories", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"Bills": 10, "Food": 25}


def test_analytics_are_scoped_to_the_current_user(client, make_expense):
    make_expense("Rent", 10, "Bills")
    bob = auth_headers_for(client, "bob", "bob@example.com")
    assert client.get("/summary", headers=bob).json()["total_expenses"] == 0
    assert client.get("/summary/categories", headers=bob).json() == {}
