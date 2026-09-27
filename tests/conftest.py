import os
import tempfile

# app.main creates tables on import, so point it at a throwaway file first.
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/import-time.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    """A TestClient backed by a fresh SQLite file per test."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def register(client, username="alice", email="alice@example.com", password="s3cret-pass"):
    return client.post(
        "/register", json={"username": username, "email": email, "password": password}
    )


def login(client, email="alice@example.com", password="s3cret-pass"):
    # OAuth2 password flow: form-encoded, and the "username" field carries the email.
    return client.post("/login", data={"username": email, "password": password})


def auth_headers_for(client, username, email, password="s3cret-pass"):
    register(client, username, email, password)
    token = login(client, email, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(client):
    return auth_headers_for(client, "alice", "alice@example.com")


@pytest.fixture
def make_expense(client, auth_headers):
    def _make(title="Lunch", amount=12.5, category="Food", headers=None):
        r = client.post(
            "/expenses",
            json={"title": title, "amount": amount, "category": category},
            headers=headers or auth_headers,
        )
        assert r.status_code == 200, r.text
        return r.json()

    return _make
