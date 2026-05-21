"""Tests for POST /internal/face/verify."""
from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest
from PIL import Image

from tests.conftest import client
from tests.face.conftest import make_face_reference

_PATCH_GET_REF = "app.services.face_service.get_face_reference"
_PATCH_DOWNLOAD = "app.services.face_service.storage.download_file"
_PATCH_LANDMARKS = "app.services.face_service._extract_landmarks"

_LIVENESS_OK = json.dumps({"blink_detected": True, "head_pose_changed": True, "challenge_passed": True})
_LIVENESS_FAIL = json.dumps({"blink_detected": False, "head_pose_changed": False, "challenge_passed": False})


def _make_jpeg(width: int = 200, height: int = 200) -> bytes:
    img = Image.new("RGB", (width, height), color=(200, 180, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _verify(employee_id: int = 1001, liveness: str = _LIVENESS_OK, image_bytes: bytes | None = None):
    data = image_bytes or _make_jpeg()
    return client.post(
        "/api/v1/internal/face/verify",
        files={"face_image": ("selfie.jpg", data, "image/jpeg")},
        data={"employee_id": employee_id, "liveness_signals": liveness},
    )


_FAKE_LANDMARKS = [(i * 0.001, i * 0.001, i * 0.001) for i in range(468)]


class TestVerifyFace:
    def test_matched_face_and_passed_liveness(self, face_ref):
        with (
            patch(_PATCH_GET_REF, return_value=face_ref),
            patch(_PATCH_DOWNLOAD, return_value=_make_jpeg()),
            patch(_PATCH_LANDMARKS, return_value=_FAKE_LANDMARKS),
        ):
            resp = _verify()

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert "face_match_score" in data
        assert "liveness_score" in data
        assert data["liveness_passed"] is True

    def test_failed_liveness_signals(self, face_ref):
        with (
            patch(_PATCH_GET_REF, return_value=face_ref),
            patch(_PATCH_DOWNLOAD, return_value=_make_jpeg()),
            patch(_PATCH_LANDMARKS, return_value=_FAKE_LANDMARKS),
        ):
            resp = _verify(liveness=_LIVENESS_FAIL)

        assert resp.status_code == 200
        assert resp.json()["data"]["liveness_passed"] is False
        assert resp.json()["data"]["liveness_score"] == 0.0

    def test_no_face_reference_returns_404(self):
        with patch(_PATCH_GET_REF, return_value=None):
            resp = _verify()

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "FACE_NOT_REGISTERED"

    def test_no_selfie_face_detected_returns_zero_score(self, face_ref):
        with (
            patch(_PATCH_GET_REF, return_value=face_ref),
            patch(_PATCH_DOWNLOAD, return_value=_make_jpeg()),
            patch(_PATCH_LANDMARKS, side_effect=[_FAKE_LANDMARKS, None]),
        ):
            resp = _verify()

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["face_match_score"] == 0.0
        assert data["face_matched"] is False
