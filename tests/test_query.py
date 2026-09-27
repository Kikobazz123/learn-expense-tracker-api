import pytest


@pytest.fixture
def seeded(make_expense):
    # Inserted in this order; created_at ascending follows it.
    make_expense("Groceries", 40, "Food")
    make_expense("Bus pass", 25, "Transport")
    make_expense("Coffee", 3.5, "Food")
    make_expense("Cinema", 12, "Entertainment")


def titles(r):
    assert r.status_code == 200, r.text
    return [e["title"] for e in r.json()]


def test_filter_by_category(client, auth_headers, seeded):
    r = client.get("/expenses", params={"category": "Food"}, headers=auth_headers)
    assert sorted(titles(r)) == ["Coffee", "Groceries"]


def test_search_is_a_case_insensitive_substring_match(client, auth_headers, seeded):
    r = client.get("/expenses", params={"search": "BUS"}, headers=auth_headers)
    assert titles(r) == ["Bus pass"]


def test_filters_combine(client, auth_headers, seeded):
    r = client.get("/expenses", params={"category": "Food", "search": "coff"}, headers=auth_headers)
    assert titles(r) == ["Coffee"]


@pytest.mark.parametrize(
    "sort_by,order,expected",
    [
        ("amount", "asc", ["Coffee", "Cinema", "Bus pass", "Groceries"]),
        ("amount", "desc", ["Groceries", "Bus pass", "Cinema", "Coffee"]),
        ("title", "asc", ["Bus pass", "Cinema", "Coffee", "Groceries"]),
        ("title", "desc", ["Groceries", "Coffee", "Cinema", "Bus pass"]),
        ("created_at", "asc", ["Groceries", "Bus pass", "Coffee", "Cinema"]),
    ],
)
def test_sorting(client, auth_headers, seeded, sort_by, order, expected):
    r = client.get("/expenses", params={"sort_by": sort_by, "order": order}, headers=auth_headers)
    assert titles(r) == expected


def test_pagination_with_skip_and_limit(client, auth_headers, seeded):
    params = {"sort_by": "amount", "order": "asc", "limit": 2}
    first = client.get("/expenses", params={**params, "skip": 0}, headers=auth_headers)
    second = client.get("/expenses", params={**params, "skip": 2}, headers=auth_headers)
    assert titles(first) == ["Coffee", "Cinema"]
    assert titles(second) == ["Bus pass", "Groceries"]


def test_default_page_size_is_ten(client, auth_headers, make_expense):
    for i in range(12):
        make_expense(f"Item {i:02d}", 1 + i, "Other")
    assert len(client.get("/expenses", headers=auth_headers).json()) == 10
