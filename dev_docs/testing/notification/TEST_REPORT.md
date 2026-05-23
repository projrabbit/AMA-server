# Notification Module — Test Report

**Date**: 2026-05-22
**Environment**: Local (no live database — DB dependency fully mocked)
**Test runner**: `uv run pytest tests/notification/ -v`
**Result**: ✅ 31 / 31 passed — 0 failed — 0 skipped
**Duration**: ~9.68s

---

## Coverage By Endpoint

| Endpoint | Tests | Result |
|----------|-------|--------|
| `GET /notifications` | 8 | ✅ All pass |
| `PUT /notifications/{notification_id}/read` | 6 | ✅ All pass |
| `PUT /notifications/read-all` | 4 | ✅ All pass |
| `GET /notifications/preferences` | 3 | ✅ All pass |
| `PUT /notifications/preferences` | 5 | ✅ All pass |
| `POST /internal/notifications/send` | 5 | ✅ All pass |

---

## Test Infrastructure

### Strategy

All service functions are patched at `app.services.notification_service.<fn>` — the point where each name is imported in the endpoint module. The `get_db` dependency is globally overridden by a `MagicMock` session in `tests/conftest.py`, so no PostgreSQL connection is needed.

`SimpleNamespace` objects are used for fixture data (`make_notification`, `make_preference`) because Pydantic's `from_attributes=True` reads arbitrary attributes, while SQLAlchemy model instances require internal ORM state.

The internal `POST /internal/notifications/send` endpoint has no JWT guard; tests call it without any `Authorization` header.

### Patch Paths Used

| Patch target | Used in |
|---|---|
| `app.services.notification_service.list_notifications` | `test_list_notifications.py` |
| `app.services.notification_service.mark_read` | `test_mark_read.py` |
| `app.services.notification_service.mark_all_notifications_read` | `test_mark_all_read.py` |
| `app.services.notification_service.get_preferences` | `test_preferences.py` |
| `app.services.notification_service.update_notification_preferences` | `test_preferences.py` |
| `app.services.notification_service.send_notifications` | `test_send_notification.py` |

### Test Fixtures

| Fixture | Role / Purpose | Notable Values |
|---------|---------------|----------------|
| `make_notification(notification_id, is_read, type_)` | Factory for `SimpleNamespace` notification objects | default `type_="checkin_approved"`, `account_id=1002` |
| `make_preference()` | Factory for `SimpleNamespace` preference object | all boolean fields default `True` |
| `as_employee` | Auth headers for employee role | `account_id=1002`, `role=employee` |
| `as_hr` | Auth headers for HR role | `account_id=1003`, `role=hr` |
| `as_admin` | Auth headers for admin role | `account_id=1001`, `role=admin` |
| `employee_account` | `SimpleNamespace` account object for employee | `account_id=1002` — used to assert service call args |
| `hr_account` | `SimpleNamespace` account object for HR | `account_id=1003` |

---

## Detailed Results

### GET /notifications — 8 tests

#### Success cases (7)

| # | Test | Status |
|---|------|--------|
| 1 | `test_employee_gets_200_with_items` — returns list with `notification_id`, `is_read` | ✅ Pass |
| 2 | `test_meta_includes_unread_count` — `meta.total`, `meta.unread_count`, `meta.total_pages` present | ✅ Pass |
| 3 | `test_admin_gets_200` — admin role accepted | ✅ Pass |
| 4 | `test_pagination_params_forwarded` — `page=2`, `limit=10` reach service kwargs | ✅ Pass |
| 5 | `test_is_read_filter_forwarded` — `is_read=false` parsed as `bool False` by service | ✅ Pass |
| 6 | `test_type_filter_forwarded` — `type=checkin_approved` forwarded as enum value | ✅ Pass |
| 7 | `test_empty_list_returns_200` — empty `data` list with 200 | ✅ Pass |

#### Auth cases (1)

| # | Test | Expected | Status |
|---|------|----------|--------|
| 8 | `test_401_when_no_token` | 401 | ✅ Pass |

---

### PUT /notifications/{notification_id}/read — 6 tests

#### Success cases (3)

| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200_with_is_read_true` — `data.notification_id` and `data.is_read` correct | ✅ Pass |
| 2 | `test_correct_id_passed_to_service` — `notification_id=999` forwarded in kwargs | ✅ Pass |
| 3 | `test_hr_can_mark_own_notification` — HR role accepted | ✅ Pass |

#### Error cases (2)

| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_404_when_notification_not_found` | 404 `NOTIFICATION_NOT_FOUND` | ✅ Pass |
| 5 | `test_403_when_wrong_owner` | 403 `FORBIDDEN` | ✅ Pass |

#### Auth cases (1)

| # | Test | Expected | Status |
|---|------|----------|--------|
| 6 | `test_401_when_no_token` | 401 | ✅ Pass |

---

### PUT /notifications/read-all — 4 tests

#### Success cases (3)

| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200_with_marked_count` — `data.marked_count=5` | ✅ Pass |
| 2 | `test_returns_zero_when_nothing_unread` — `marked_count=0` valid | ✅ Pass |
| 3 | `test_account_id_passed_to_service` — `account_id` kwarg matches employee fixture | ✅ Pass |

#### Auth cases (1)

| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_401_when_no_token` | 401 | ✅ Pass |

---

### GET /notifications/preferences — 3 tests

#### Success cases (2)

| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200_with_all_fields` — all preference fields present in response | ✅ Pass |
| 2 | `test_admin_gets_200` — admin role accepted | ✅ Pass |

#### Auth cases (1)

| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_401_when_no_token` | 401 | ✅ Pass |

---

### PUT /notifications/preferences — 5 tests

#### Success cases (2)

| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200_updated_true` — `data.updated=True` | ✅ Pass |
| 2 | `test_request_body_forwarded_to_service` — all 8 boolean fields forwarded correctly | ✅ Pass |

#### Validation cases (1)

| # | Test | Expected | Status |
|---|------|----------|--------|
| 3 | `test_422_when_missing_required_field` — `push_enabled` omitted | 422 | ✅ Pass |

#### Auth cases (1)

| # | Test | Expected | Status |
|---|------|----------|--------|
| 4 | `test_401_when_no_token` | 401 | ✅ Pass |

---

### POST /internal/notifications/send — 5 tests

#### Success cases (4)

| # | Test | Status |
|---|------|--------|
| 1 | `test_returns_200_with_sent_and_failed_counts` — `sent_count=2`, `failed_count=0` | ✅ Pass |
| 2 | `test_failed_count_reflects_unknown_accounts` — `sent_count=1`, `failed_count=1` | ✅ Pass |
| 3 | `test_no_auth_required` — no `Authorization` header, still 200 | ✅ Pass |
| 4 | `test_payload_forwarded_to_service` — `account_ids`, `type.value`, `title` all correct | ✅ Pass |

#### Validation cases (1)

| # | Test | Expected | Status |
|---|------|----------|--------|
| 5 | `test_422_when_invalid_type` — unknown enum value | 422 | ✅ Pass |
| 6 | `test_422_when_missing_required_fields` — body with only `account_ids` | 422 | ✅ Pass |

---

## Security Behaviours Verified

| Behaviour | Verified By |
|-----------|-------------|
| All authenticated endpoints reject missing token with 401 | Tests #8 (list), #6 (mark read), #4 (mark all read), #3 (get prefs), #4 (update prefs) |
| Owner check on single-notification mark-read: 403 if `account_id` mismatch | `test_403_when_wrong_owner` |
| Internal send endpoint requires no auth (called by internal services only) | `test_no_auth_required` |

---

## Known Limitations Of This Test Run

1. **No real database** — all service functions are patched; repository queries never run.
2. **No push delivery tested** — `send_notifications` only creates in-app `Notification` rows; FCM/APNs integration is out of scope.
3. **Route conflict correctness** — the static `/read-all` path being registered before `/{notification_id}/read` is validated implicitly (tests hit both routes correctly), not by an explicit route-ordering test.

---

## How To Run

```bash
uv run pytest tests/notification/ -v
uv run pytest tests/notification/ -v --cov=app --cov-report=term-missing
```
