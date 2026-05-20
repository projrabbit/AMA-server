# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Development server
uv run fastapi dev app/main.py

# Install dependencies (including dev group)
uv sync --group dev

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/auth/test_login.py -v

# Run a single test by class and name
uv run pytest tests/auth/test_login.py::TestLoginSuccess::test_admin_login_returns_200 -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=term-missing

# Stop on first failure
uv run pytest tests/ -x

# Alembic — generate a new migration
uv run alembic revision --autogenerate -m "description"

# Alembic — apply migrations
uv run alembic upgrade head

# Verify the app imports cleanly
uv run python -c "from app.main import app"

# Start infrastructure (Redis + MinIO)
docker compose up -d redis minio
```

## Architecture

### Request/Response Layer

All endpoints return a standard envelope defined in `app/schemas/common.py`:
- Success: `{"success": true, "data": {...}, "meta": null}`
- Error: `{"success": false, "error": {"code": "...", "message": "...", "details": {}}}`

A global `HTTPException` handler in `app/main.py` converts FastAPI's native exceptions to this format automatically.

### Auth Layer (implemented)

The auth stack is layered: `core/security.py` → `repositories/auth_repository.py` → `services/auth_service.py` → `api/v1/endpoints/auth.py`. Access guards live in `api/dependencies.py`.

**Tokens**: Dual-token (access 24h + refresh 7d), each JWT carries a UUID4 `jti`. An in-memory `dict[str, float]` in `core/security.py` blacklists revoked JTIs. Logout blacklists both tokens; refresh only issues a new access token.

**Role guards**: `api/dependencies.py` exposes `CurrentAccount` and pre-composed type-alias dependencies (`EmployeeAccount`, `HROrAdminAccount`, `ManagerOrAboveAccount`, `AdminAccount`) built via `_role_guard(*roles)`. Inject these as parameter type hints — FastAPI resolves them automatically.

**Role values**: `AccountRole` enum in `app/models/business.py` — `employee`, `hr`, `manager`, `admin`.

### Database / Models

Two PostgreSQL schemas: `business` (HR/attendance data) and `gis` (geofence zones). Each has its own model file — `app/models/business.py` and `app/models/gis.py`. Both are imported in `app/models/__init__.py`, which is the single import Alembic reads.

Alembic's `env.py` uses `include_name` / `include_object` hooks to restrict migrations to only these two schemas. When adding a new model, import it in `app/models/__init__.py` or it won't appear in `alembic revision --autogenerate` output.

All models use SQLAlchemy 2.x `Mapped` / `mapped_column` syntax. Foreign keys reference the schema-qualified table name (e.g., `"business.employees.employee_id"`).

### Adding a New Endpoint Module

1. Create `app/repositories/<module>_repository.py` — raw DB queries only, no business logic.
2. Create `app/services/<module>_service.py` — orchestrates repository calls, raises `HTTPException` on errors.
3. Create `app/api/v1/endpoints/<module>.py` — thin router, delegates to the service.
4. Register in `app/api/v1/router.py` via `api_router.include_router(...)`.
5. Add request/response schemas in `app/schemas/<module>.py`; wrap responses in `SuccessResponse[T]`.

### Testing Strategy

Tests use FastAPI's `TestClient` with the `get_db` dependency globally overridden by a `MagicMock` session — no real PostgreSQL connection needed.

**Fixture pattern**: Use `SimpleNamespace(...)` for account/employee test objects, not SQLAlchemy model instances. SQLAlchemy's `__init__` bootstraps internal state (`_sa_instance_state`); bypassing it with `__new__` or bare object construction causes `AttributeError` inside the ORM. `SimpleNamespace` works because Pydantic's `from_attributes=True` only reads attributes.

**Patch target rule**: Patch where the name is bound, not where it is defined.
- `dependencies.py` imports `get_account_by_id` at module level → patch `"app.api.dependencies.get_account_by_id"`.
- `auth_service.py::refresh_access_token` imports `get_account_by_id` inline (inside the function) → patch `"app.repositories.auth_repository.get_account_by_id"`.

### Implementation Progress

See `dev_docs/API_IMPLEMENTATION_CHECKLIST.md` for the full endpoint checklist (5/47 complete as of initial implementation — auth module only).

Full API specification lives in `dev_docs/FULL_API_DOCS.md` (47 endpoints across 9 modules).

Test documentation lives in `dev_docs/testing/authen/` (README + TEST_REPORT).
