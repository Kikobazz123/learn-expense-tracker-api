from tests.conftest import login, register


def test_register_returns_public_fields(client):
    r = register(client)
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "password" not in body


def test_register_rejects_invalid_email(client):
    r = client.post("/register", json={"username": "a", "email": "nope", "password": "x"})
    assert r.status_code == 422


def test_login_issues_bearer_token(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_wrong_password_is_401(client):
    register(client)
    r = login(client, password="wrong")
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password"


def test_login_unknown_email_is_401(client):
    assert login(client, email="ghost@example.com").status_code == 401


def test_protected_routes_require_a_token(client):
    assert client.get("/me").status_code == 401
    assert client.get("/expenses").status_code == 401
    assert client.get("/summary").status_code == 401


def test_protected_route_rejects_a_bad_token(client):
    r = client.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_me_returns_the_current_user(client, auth_headers):
    r = client.get("/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"


def test_me_does_not_expose_the_password_hash(client, auth_headers):
    body = client.get("/me", headers=auth_headers).json()
    assert "password" not in body


def test_duplicate_registration_is_a_client_error(client):
    register(client)
    assert register(client).status_code == 400
    assert register(client, username="alice2").status_code == 400  # same email
    assert register(client, email="other@example.com").status_code == 400  # same username
