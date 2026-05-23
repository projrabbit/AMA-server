# Notification Test Suite

Test files for `Module 6: Notification` (`/api/v1/notifications/*` and `/api/v1/internal/notifications/*`).

## Files

| File | Endpoint | Tests |
|------|----------|-------|
| `tests/notification/test_list_notifications.py` | `GET /notifications` | 8 |
| `tests/notification/test_mark_read.py` | `PUT /notifications/{notification_id}/read` | 6 |
| `tests/notification/test_mark_all_read.py` | `PUT /notifications/read-all` | 4 |
| `tests/notification/test_preferences.py` | `GET /notifications/preferences` + `PUT /notifications/preferences` | 8 |
| `tests/notification/test_send_notification.py` | `POST /internal/notifications/send` | 5 |

**Total: 31 tests, all passing.**

## How To Run

```bash
uv run pytest tests/notification/ -v
uv run pytest tests/notification/test_list_notifications.py -v
uv run pytest tests/notification/ -v --cov=app --cov-report=term-missing
uv run pytest tests/notification/ -x
```

## Architecture

```
TestClient (no live server)
    └── app.dependency_overrides[get_db] = MagicMock session
    └── unittest.mock.patch() for service functions (not repository)
    └── SimpleNamespace fixtures (Pydantic from_attributes=True compatible)
    └── Route order matters: /read-all and /preferences (static) registered
        before /{notification_id}/read (parametric) in notifications.py
    └── Internal endpoint (POST /internal/notifications/send) has no JWT guard —
        tested without any auth headers
```

## Patch Paths Quick Reference

```python
# Service-level patches (service functions imported at module level in endpoints)
"app.services.notification_service.list_notifications"
"app.services.notification_service.mark_read"
"app.services.notification_service.mark_all_notifications_read"
"app.services.notification_service.get_preferences"
"app.services.notification_service.update_notification_preferences"
"app.services.notification_service.send_notifications"
```
