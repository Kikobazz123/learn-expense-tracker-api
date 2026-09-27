# Expense Tracker API

[![CI](https://github.com/Kikobazz123/learn-expense-tracker-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Kikobazz123/learn-expense-tracker-api/actions/workflows/ci.yml)

A REST API for tracking personal expenses, with JWT auth, per-user data, filtering,
sorting, pagination and spending summaries. A learning build: written to practise
backend fundamentals in FastAPI end to end, from auth to tests to CI.

Built by **[Lordmark Dorgu](https://github.com/Kikobazz123)** · MIT licensed.

![Swagger UI](screenshots/Swagger-Homepage.png)

---

## The problem it solves

Most expense-tracker tutorials stop at CRUD on a single table. The parts that matter
in a real API are the ones around it: every query scoped to the signed-in user,
validation that rejects nonsense at the edge, list endpoints that page and sort, and
tests that prove one user can never read or change another's data. This project is
built around those parts.

## Stack

Python 3.10 · FastAPI · SQLAlchemy 2.0 · SQLite · Pydantic v2 · OAuth2 password flow
with JWT (python-jose) · bcrypt via passlib · pytest + httpx `TestClient` · ruff ·
GitHub Actions

## Architecture

```
app/
  main.py       routes: auth, expense CRUD, list with filters, summaries
  auth.py       JWT creation, get_current_user dependency
  security.py   bcrypt hashing and verification
  models.py     SQLAlchemy models: User 1-N Expense
  schemas.py    Pydantic request/response models, ExpenseCategory enum
  database.py   engine and get_db session dependency (DATABASE_URL)
tests/          pytest suite, one temporary SQLite database per test
```

| Method | Path | Auth | What it does |
|---|---|---|---|
| POST | `/register` | – | Create a user (400 if the username or email is taken) |
| POST | `/login` | – | Form-encoded OAuth2 login; `username` carries the email. Returns a bearer token |
| GET | `/me` | Bearer | The current user (id, username, email) |
| POST | `/expenses` | Bearer | Create an expense |
| GET | `/expenses` | Bearer | List your expenses: `category`, `search`, `sort_by` (`amount`, `created_at`, `title`), `order`, `skip`, `limit` (default 10) |
| PUT | `/expenses/{id}` | Bearer | Update one of your expenses (404 otherwise) |
| DELETE | `/expenses/{id}` | Bearer | Delete one of your expenses (404 otherwise) |
| GET | `/summary` | Bearer | Count, total and average of your expenses |
| GET | `/summary/categories` | Bearer | Total spent per category |

Categories are a fixed enum: Food, Transport, Shopping, Bills, Entertainment, Health,
Other. Amounts must be greater than zero and titles 2–100 characters.

## Run locally

```bash
git clone https://github.com/Kikobazz123/learn-expense-tracker-api.git
cd learn-expense-tracker-api
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Interactive docs are then at `$BASE_URL/docs` (Swagger) and `$BASE_URL/redoc`.

Configuration comes from the environment; every variable is optional and documented
in [`.env.example`](.env.example):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./expenses.db` | SQLAlchemy database URL |
| `SECRET_KEY` | a development value | Signs JWTs. **Set your own anywhere the API is reachable** |
| `BASE_URL` | local uvicorn address | Where the API is served; used in these docs |

## Tests

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

34 tests covering registration and login, token checks on protected routes, expense
CRUD, cross-user isolation, every filter, sort and page option, and the summaries.
Each test gets its own temporary SQLite file through a `get_db` dependency override,
so tests never share state or touch `expenses.db`. CI runs ruff and pytest on every
push.

## Design decisions and trade-offs

- **Ownership is enforced in the query, not after it.** Update and delete filter on
  both the expense id and `owner_id`, so another user's expense is indistinguishable
  from a missing one (404). A test checks this directly.
- **Response models decide what leaves the API.** Writing the tests found that `/me`
  returned the raw ORM user, bcrypt hash included, because the route had no
  `response_model`. It now uses `UserResponse`; the test that caught it stays.
- **Validation lives in the schema.** A second, unconstrained `ExpenseCreate` further
  down `schemas.py` had silently replaced the real one, so negative amounts were
  accepted. The duplicate is gone and tests pin the constraints.
- **Duplicate sign-ups are a client error.** They used to surface as a 500 from the
  database's unique constraint; the route now checks first and returns 400.
- **SQLite by default.** Zero setup for a learning project. `DATABASE_URL` makes the
  engine swappable, but tables are created at startup with `create_all` rather than
  migrations, which would be the first thing to change for a real deployment.
- **Known gaps, left visible:** `limit` has no upper bound, an unknown `sort_by` is
  ignored rather than rejected, and timestamps use the deprecated `datetime.utcnow`.

More screenshots: [register](screenshots/register-endpoint.png) ·
[login](screenshots/login-endpoint.png) · [summary](screenshots/expenses-endpoint.png)
