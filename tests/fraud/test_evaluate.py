"""Tests for POST /internal/fraud/evaluate."""
from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from tests.conftest import client
from tests.fraud.conftest import make_device

_FACE_REF = SimpleNamespace(face_object_key="faces/employee_1001/reference.jpg")

_PATCH_GET_DEVICE = "app.services.fraud_service.get_device_by_fingerprint_and_employee"
_PATCH_GET_RECENT = "app.services.fraud_service.get_recent_device_records"
_PATCH_GET_FACE_REF = "app.services.fraud_service.get_face_reference"
_PATCH_DOWNLOAD = "app.services.fraud_service.storage.download_file"
_PATCH_LANDMARKS = "app.services.fraud_service._extract_landmarks"
_PATCH_COSINE = "app.services.fraud_service._cosine_similarity"
_PATCH_LIVENESS = "app.services.fraud_service._liveness_score"

_BASE_PAYLOAD = {
    "employee_id": 1001,
    "device_fingerprint": "abc-device-fp",
    "latitude": 10.772123,
    "longitude": 106.657890,
    "altitude": 12.5,
    "gps_accuracy": 5.2,
    "timestamp": "2026-05-20T08:02:10+07:00",
    "is_mock_location": False,
    "face_image_object_key": "selfies/2026/05/20/1001.jpg",
    "liveness_signals": {
        "blink_detected": True,
        "head_pose_changed": True,
        "challenge_passed": True,
    },
}

_TRUSTED_DEVICE = make_device(is_trusted=True)


def _post(payload: dict):
    return client.post("/api/v1/internal/fraud/evaluate", json=payload)


class TestEvaluateFraudSuccess:
    def test_returns_200_clean_verdict(self):
        landmarks = [(0.1, 0.2, 0.3)] * 468
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=_FACE_REF),
            patch(_PATCH_DOWNLOAD, return_value=b"fake-image-bytes"),
            patch(_PATCH_LANDMARKS, return_value=landmarks),
            patch(_PATCH_COSINE, return_value=0.95),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(_BASE_PAYLOAD)

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["mock_location_detected"] is False
        assert data["gps_spoofing_detected"] is False
        assert data["buddy_punch_suspected"] is False
        assert data["unknown_device"] is False
        assert data["face_mismatch_detected"] is False
        assert data["liveness_failed"] is False
        assert data["confidence_score"] == 100.0
        assert data["reason"] is None
        assert data["flags"] == []

    def test_returns_200_no_auth_required(self):
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(_BASE_PAYLOAD)
        assert resp.status_code == 200


class TestEvaluateFraudMockLocation:
    def test_mock_location_detected_when_flag_is_true(self):
        payload = {**_BASE_PAYLOAD, "is_mock_location": True}
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(payload)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["mock_location_detected"] is True
        assert "mock_location" in data["flags"]
        assert data["confidence_score"] == 30.0  # 100 - 40(mock) - 30(face_mismatch, no ref)
        assert data["reason"] == "mock_location"


class TestEvaluateFraudGpsSpoofing:
    def test_gps_spoofing_detected_when_speed_exceeds_threshold(self):
        payload = {
            **_BASE_PAYLOAD,
            "raw_signals": {"provider": "gps", "speed_mps": 10.0},
        }
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(payload)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["gps_spoofing_detected"] is True
        assert "gps_spoofing" in data["flags"]

    def test_no_gps_spoofing_when_speed_is_low(self):
        payload = {
            **_BASE_PAYLOAD,
            "raw_signals": {"provider": "gps", "speed_mps": 0.3},
        }
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(payload)

        assert resp.status_code == 200
        assert resp.json()["data"]["gps_spoofing_detected"] is False


class TestEvaluateFraudUnknownDevice:
    def test_unknown_device_when_not_registered(self):
        with (
            patch(_PATCH_GET_DEVICE, return_value=None),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(_BASE_PAYLOAD)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["unknown_device"] is True
        assert "unknown_device" in data["flags"]

    def test_unknown_device_when_device_not_trusted(self):
        untrusted = make_device(is_trusted=False)
        with (
            patch(_PATCH_GET_DEVICE, return_value=untrusted),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(_BASE_PAYLOAD)

        assert resp.status_code == 200
        assert resp.json()["data"]["unknown_device"] is True


class TestEvaluateFraudBuddyPunch:
    def test_buddy_punch_suspected_when_device_used_by_other_employee(self):
        other_record = object()
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[other_record]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(_BASE_PAYLOAD)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["buddy_punch_suspected"] is True
        assert "buddy_punch" in data["flags"]

    def test_no_buddy_punch_when_device_not_shared(self):
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(_BASE_PAYLOAD)

        assert resp.status_code == 200
        assert resp.json()["data"]["buddy_punch_suspected"] is False


class TestEvaluateFraudFaceVerification:
    def test_face_mismatch_when_no_face_reference(self):
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(_BASE_PAYLOAD)

        assert resp.status_code == 200
        assert resp.json()["data"]["face_mismatch_detected"] is True

    def test_face_mismatch_when_score_below_threshold(self):
        landmarks = [(0.1, 0.2, 0.3)] * 468
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=_FACE_REF),
            patch(_PATCH_DOWNLOAD, return_value=b"img"),
            patch(_PATCH_LANDMARKS, return_value=landmarks),
            patch(_PATCH_COSINE, return_value=0.5),
            patch(_PATCH_LIVENESS, return_value=(0.9, True)),
        ):
            resp = _post(_BASE_PAYLOAD)

        assert resp.status_code == 200
        assert resp.json()["data"]["face_mismatch_detected"] is True

    def test_liveness_failed_when_signals_insufficient(self):
        payload = {
            **_BASE_PAYLOAD,
            "liveness_signals": {"blink_detected": False, "head_pose_changed": False, "challenge_passed": False},
        }
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
        ):
            resp = _post(payload)

        assert resp.status_code == 200
        assert resp.json()["data"]["liveness_failed"] is True


class TestEvaluateFraudConfidenceScore:
    def test_confidence_score_deducted_for_all_flags(self):
        other_record = object()
        untrusted = make_device(is_trusted=False)
        payload = {**_BASE_PAYLOAD, "is_mock_location": True}
        with (
            patch(_PATCH_GET_DEVICE, return_value=untrusted),
            patch(_PATCH_GET_RECENT, return_value=[other_record]),
            patch(_PATCH_GET_FACE_REF, return_value=None),
            patch(_PATCH_LIVENESS, return_value=(0.0, False)),
        ):
            resp = _post(payload)

        assert resp.status_code == 200
        assert resp.json()["data"]["confidence_score"] == 0.0

    def test_confidence_score_is_100_when_no_flags(self):
        landmarks = [(0.1, 0.2, 0.3)] * 468
        with (
            patch(_PATCH_GET_DEVICE, return_value=_TRUSTED_DEVICE),
            patch(_PATCH_GET_RECENT, return_value=[]),
            patch(_PATCH_GET_FACE_REF, return_value=_FACE_REF),
            patch(_PATCH_DOWNLOAD, return_value=b"img"),
            patch(_PATCH_LANDMARKS, return_value=landmarks),
            patch(_PATCH_COSINE, return_value=0.99),
            patch(_PATCH_LIVENESS, return_value=(1.0, True)),
        ):
            resp = _post(_BASE_PAYLOAD)

        assert resp.status_code == 200
        assert resp.json()["data"]["confidence_score"] == 100.0
