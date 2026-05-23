# Fraud Detection Test Suite

Test files for `Module 4: Fraud Detection` (`/api/v1/fraud/*` and `/api/v1/internal/fraud/*`).

## Files

| File | Endpoint | Tests |
|------|----------|-------|
| `tests/fraud/test_evaluate.py` | `POST /internal/fraud/evaluate` | 14 |
| `tests/fraud/test_fraud_records.py` | `GET /fraud/records` | 8 |
| `tests/fraud/test_fraud_detail.py` | `GET /fraud/records/{fraud_id}` | 6 |

**Total: 28 tests, all passing.**

## How To Run

```bash
uv run pytest tests/fraud/ -v
uv run pytest tests/fraud/test_evaluate.py -v
uv run pytest tests/fraud/test_fraud_records.py -v
uv run pytest tests/fraud/test_fraud_detail.py -v
uv run pytest tests/fraud/ -v --cov=app --cov-report=term-missing
uv run pytest tests/fraud/ -x
```

## Architecture

```
TestClient (no live server)
    └── app.dependency_overrides[get_db] = MagicMock session
    └── unittest.mock.patch() for repository functions and storage
    └── SimpleNamespace fixtures (Pydantic from_attributes=True compatible)
    └── Internal endpoint (POST /evaluate) has no auth — tested without headers
    └── Face service helpers (_extract_landmarks, _cosine_similarity, _liveness_score)
        are imported at module level in fraud_service and patched at
        "app.services.fraud_service.<helper_name>"
```

## Patch Paths Quick Reference

```python
# evaluate endpoint — sub-function patches
"app.services.fraud_service.get_device_by_fingerprint_and_employee"
"app.services.fraud_service.get_recent_device_records"
"app.services.fraud_service.get_face_reference"
"app.services.fraud_service.storage.download_file"
"app.services.fraud_service._extract_landmarks"
"app.services.fraud_service._cosine_similarity"
"app.services.fraud_service._liveness_score"

# list and detail endpoints — service-level patches
"app.services.fraud_service.list_fraud_records"
"app.services.fraud_service.get_fraud_record_detail"

# auth dependency
"app.api.dependencies.get_account_by_id"
```
