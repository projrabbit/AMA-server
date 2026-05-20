# Module Complete

After finishing implementation and tests for a module, run this workflow to keep `dev_docs/` in sync.

## What to do

### 1 — Update the implementation checklist

Open `dev_docs/API_IMPLEMENTATION_CHECKLIST.md` and for every endpoint just implemented:

- Change `⬜` → `✅`
- Update the **Progress** counter at the top (e.g. `5 / 47` → `12 / 47`)
- Fill in the **Notes** column with one-line summary of anything non-obvious (e.g. which service raises which error code, or a dependency that must exist)
- Update the **Files written** block under the module heading to list all new files created

### 2 — Create the test docs directory

Create `dev_docs/testing/<module_slug>/` where `<module_slug>` is the lowercase module name with no spaces (e.g. `geofence`, `admin`, `attendance`).

Write two files into that directory:

#### `README.md`

Use this exact structure:

```markdown
# <Module Name> Test Suite

Test files for `Module N: <Module Name>` (`/api/v1/<prefix>/*`).

## Files

| File | Endpoint | Tests |
|------|----------|-------|
| `tests/<slug>/test_<endpoint>.py` | `METHOD /path` | N |
...

**Total: N tests, all passing.**

## How To Run

```bash
uv run pytest tests/<slug>/ -v
uv run pytest tests/<slug>/test_<file>.py -v
uv run pytest tests/<slug>/ -v --cov=app --cov-report=term-missing
uv run pytest tests/<slug>/ -x
```

## Architecture

```
TestClient (no live server)
    └── app.dependency_overrides[get_db] = MagicMock session
    └── unittest.mock.patch() for repository functions
    └── SimpleNamespace fixtures (Pydantic from_attributes=True compatible)
    └── <any module-specific notes>
```

## Patch Paths Quick Reference

```python
# list the exact patch strings used in this module's tests
"app.repositories.<module>_repository.<function>"
"app.services.<module>_service.<function>"
"app.api.dependencies.<function>"
```
```

#### `TEST_REPORT.md`

Use this exact structure:

```markdown
# <Module Name> Module — Test Report

**Date**: YYYY-MM-DD
**Environment**: Local (no live database — DB dependency fully mocked)
**Test runner**: `uv run pytest tests/<slug>/ -v`
**Result**: ✅ N / N passed — 0 failed — 0 skipped
**Duration**: ~Xs

---

## Coverage By Endpoint

| Endpoint | Tests | Result |
|----------|-------|--------|
| `METHOD /path` | N | ✅ All pass |

---

## Test Infrastructure

### Strategy
<describe mock strategy and any module-specific fixtures>

### Patch Paths Used
| Patch target | Used in |
|---|---|
| `app.services.<module>_service.<fn>` | <test files> |

### Test Fixtures
<table of fixture names, their role/purpose, and notable values>

---

## Detailed Results

### METHOD /path — N tests

#### Success cases (N)
| # | Test | Status |
|---|------|--------|
| 1 | <test description> | ✅ Pass |

#### Error cases (N)
| # | Test | Expected | Status |
|---|------|----------|--------|
| N | <test description> | NNN `ERROR_CODE` | ✅ Pass |

---

## Security Behaviours Verified  *(omit section if none)*

| Behaviour | Verified By |
|-----------|-------------|
| <behaviour> | Test #N |

---

## Known Limitations Of This Test Run

1. **No real database** — repository functions are mocked.
2. <any other limitations>

---

## How To Run

```bash
uv run pytest tests/<slug>/ -v
uv run pytest tests/<slug>/ -v --cov=app --cov-report=term-missing
```
```

### 3 — Run the tests and capture the real numbers

```bash
uv run pytest tests/<slug>/ -v
```

Copy the actual pass/fail counts and duration into `TEST_REPORT.md` before committing. Never write "all passing" without running them first.

### 4 — Verify checklist accuracy

Re-read the checklist entry you just updated and confirm:
- Every file listed under **Files written** actually exists on disk
- The progress counter matches the real count of ✅ rows across all modules
- Any endpoint that still has a known blocker (missing model, missing package) keeps ⬜ and gets a note in the Notes column

---

## Example invocation

When a user says "I just finished Module 3 — Geofence", work through steps 1–4 in order without skipping.
