# Implement Module

Implement a complete API module end-to-end, following the project's established layered architecture.

## Input

The user names the module to implement (e.g. "Module 3 — Geofence", "Module 9 — Admin Management"). Read `dev_docs/FULL_API_DOCS.md` for the full endpoint specification of that module before writing any code.

---

## Step 0 — Brainstorm

Before reading any code, think out loud about the module. Write a short analysis directly in your response covering:

**Endpoints inventory**
List every endpoint in this module with its method, path, and one-line purpose. Count them.

**Data flow**
Trace the happy path for the most complex endpoint: what comes in, what DB tables are touched, what goes out.

**Dependencies**
- Which other modules must be implemented first (e.g. Attendance needs Geofence)?
- Which models must exist in `business.py` / `gis.py`?
- Which Python packages must be in `pyproject.toml`?

**Authorization matrix**
For each endpoint, state which role(s) can call it (`employee`, `hr`, `manager`, `admin`) and which role guard alias from `dependencies.py` maps to that.

**Edge cases and constraints**
List the non-obvious validation rules, uniqueness constraints, soft-delete semantics, conflict checks, or pagination limits the docs describe. These become test cases later.

**Risks and unknowns**
Anything unclear in the spec, any missing information, or any part of the implementation likely to be tricky. Flag them explicitly so the user can clarify before work starts.

Present the brainstorm as structured prose or bullet points — not code. Ask the user to confirm or clarify before moving to Step 1.

---

## Step 1 — Plan

After the user confirms the brainstorm, produce a concrete implementation plan. Present it as a numbered task list with one line per file to create or modify:

```
1. app/models/business.py          — ADD <ModelName>: <fields summary>
2. app/models/__init__.py          — import <ModelName>
3. alembic migration               — autogenerate after model added
4. app/schemas/<module>.py         — CREATE: <list of request/response models>
5. app/repositories/<module>_repository.py  — CREATE: <list of functions>
6. app/services/<module>_service.py         — CREATE: <list of functions>
7. app/api/v1/endpoints/<module>.py         — CREATE: <N route handlers>
8. app/api/v1/router.py            — REGISTER: prefix=/<prefix>
9. tests/<slug>/conftest.py        — ADD fixtures: <fixture names>
10. tests/<slug>/test_<x>.py       — N tests for <endpoint>
...
```

Also list:
- **Skipped items**: anything in Step 0's dependency or package list that is NOT being implemented now, and why.
- **Open questions**: anything still unclear that would block a specific task above.

Wait for explicit user approval of this plan before writing any code. Do not start Step 2 until the user says to proceed.

---

## Step 2 — Read before writing

Before touching any file:

1. Read `dev_docs/FULL_API_DOCS.md` — find the module section, read every endpoint's request schema, response schema, error table, and authorization requirements.
2. Read `dev_docs/API_IMPLEMENTATION_CHECKLIST.md` — check which endpoints are still `⬜` and note any listed blockers (missing models, missing packages).
3. Read `app/models/business.py` and `app/models/gis.py` — confirm every model the module needs actually exists. If a model is missing, add it in Step 3.
4. Read `app/api/dependencies.py` — note which role-guard type aliases are available (`EmployeeAccount`, `HROrAdminAccount`, `ManagerOrAboveAccount`, `AdminAccount`).
5. Read `app/schemas/common.py` — confirm `SuccessResponse[T]` and `ErrorResponse` are available.

Do not proceed past Step 2 until you have read all five items above.

---

## Step 3 — Add missing DB models (if any)

If the checklist or Step 0 identified missing models:

- Add the model to `app/models/business.py` (or `app/models/gis.py` for spatial data).
- Use SQLAlchemy 2.x `Mapped` / `mapped_column` syntax.
- Foreign keys must reference the schema-qualified table name, e.g. `"business.employees.employee_id"`.
- Add the import to `app/models/__init__.py` — Alembic reads only from there.
- Generate and apply the migration:
  ```bash
  uv run alembic revision --autogenerate -m "<description>"
  uv run alembic upgrade head
  ```

---

## Step 4 — Schemas (`app/schemas/<module>.py`)

Create `app/schemas/<module>.py`. Include:

- **Request models** — one Pydantic model per endpoint that accepts a body. Add `field_validator` for any business-rule validation (password strength, date ranges, etc.). Validation errors must surface as HTTP 422 without reaching the service layer.
- **Response sub-objects** — small models for nested data (e.g. `EmployeeInfo`, `DepartmentInfo`). Set `model_config = ConfigDict(from_attributes=True)` on every model that will be constructed from a SQLAlchemy / SimpleNamespace object.
- **Response data objects** — one model per endpoint response shape (e.g. `EmployeeListData`, `EmployeeDetailData`).
- All responses are wrapped by `SuccessResponse[T]` from `app/schemas/common.py`; define only the `T` part here.

---

## Step 5 — Repository (`app/repositories/<module>_repository.py`)

Create the repository file. Rules:

- Raw DB queries only. No `HTTPException`, no business logic.
- Use SQLAlchemy 2.x `select()` / `update()` / `delete()` style.
- Use `joinedload` / `selectinload` for any relationship that the service or schema will access.
- Every function takes `db: Session` as its first argument.
- Return ORM objects or `None`; never raise.

Typical functions to write per module:

| Pattern | Example |
|---------|---------|
| List with optional filters | `get_<entities>(db, *, filter_a, filter_b, skip, limit)` |
| Fetch single by PK | `get_<entity>_by_id(db, id)` |
| Create | `create_<entity>(db, **fields)` |
| Update | `update_<entity>(db, id, **fields)` |
| Soft-delete | `deactivate_<entity>(db, id)` |

---

## Step 6 — Service (`app/services/<module>_service.py`)

Create the service file. Rules:

- Imports repository functions at the **top of the file** (module-level), not inside function bodies, unless the function is called in a circular-import scenario.
- Raises `HTTPException` with the exact `detail` dict matching the error codes in `FULL_API_DOCS.md`:
  ```python
  raise HTTPException(
      status_code=404,
      detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
  )
  ```
- Calls `create_audit_log` from `app/repositories/auth_repository` for any state-changing operation that the docs say should be audited.
- Returns schema data objects (the `T` in `SuccessResponse[T]`), not raw ORM objects.

---

## Step 7 — Endpoints (`app/api/v1/endpoints/<module>.py`)

Create the router file:

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import SuccessResponse
from app.schemas.<module> import ...
from app.services import <module>_service
from app.api.dependencies import CurrentAccount, AdminAccount, ...  # whichever roles apply

router = APIRouter()
```

Rules:

- Each route handler is thin: validate input (Pydantic does this), call one service function, return `SuccessResponse(data=result)`.
- Use `Request` to extract `request.client.host` for audit log `ip_address` wherever the docs require it.
- Apply the correct role guard from `dependencies.py` as the type annotation of the account parameter.
- Pagination: accept `skip: int = 0, limit: int = Query(default=20, le=100)` where the docs specify a paginated list.

---

## Step 6 — Register router (`app/api/v1/router.py`)

Add one line:

```python
from app.api.v1.endpoints import <module>
api_router.include_router(<module>.router, prefix="/<prefix>", tags=["<tag>"])
```

Use the URL prefix exactly as shown in `FULL_API_DOCS.md`.

---

## Step 7 — Smoke test

```bash
uv run python -c "from app.main import app"
uv run fastapi dev app/main.py
```

The server must start with no import errors. Hit `GET /docs` and confirm the new routes appear in the Swagger UI.

---

## Step 8 — Write tests

For every endpoint just implemented, write a pytest file at `tests/<module_slug>/test_<endpoint_name>.py`.

Follow the established test patterns from `tests/auth/`:

- Use `SimpleNamespace(...)` for fixture objects — never instantiate SQLAlchemy models directly.
- The `get_db` override is already set up in `tests/conftest.py`; reuse `client` from there.
- Patch repository functions at the point where the name is **bound**:
  - Module-level import in `dependencies.py` → patch `"app.api.dependencies.<fn>"`
  - Module-level import in `<module>_service.py` → patch `"app.services.<module>_service.<fn>"`
  - Inline import inside a service function → patch `"app.repositories.<module>_repository.<fn>"`
- Write success cases and error cases for each endpoint.
- For endpoints that require authorization, include a test for missing/invalid token (expect 401) and a test for wrong role (expect 403).

Run the tests:

```bash
uv run pytest tests/<module_slug>/ -v
```

All tests must pass before proceeding.

---

## Step 9 — Run `/module-done`

After all tests pass, invoke `/module-done` to update `API_IMPLEMENTATION_CHECKLIST.md` and create the `dev_docs/testing/<slug>/` documentation.
