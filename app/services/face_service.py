from __future__ import annotations

import io
import json
from datetime import date

import cv2
import mediapipe as mp
import numpy as np
from fastapi import HTTPException, status
from PIL import Image
from sqlalchemy.orm import Session

from app.core import storage
from app.models.business import AuditActionType
from app.repositories.auth_repository import create_audit_log
from app.repositories.face_repository import (
    delete_face_reference,
    get_face_reference,
    upsert_face_reference,
)
from app.repositories.admin_repository import get_employee_by_id
from app.schemas.face import DeleteFaceData, FaceStatusData, RegisterFaceData, VerifyFaceData

_FACE_MATCH_THRESHOLD = 0.92
_LIVENESS_PASS_THRESHOLD = 0.67
_MIN_IMAGE_DIMENSION = 128
_MAX_FILE_BYTES = 5 * 1024 * 1024


# ── Image validation helpers ──────────────────────────────────────────────────

def _load_pil_image(file_bytes: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
        img = Image.open(io.BytesIO(file_bytes))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "Invalid image file", "details": {}},
        )
    if img.format not in ("JPEG", "PNG"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "Only JPEG and PNG are accepted", "details": {}},
        )
    return img


def _bytes_to_bgr(file_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(file_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _detect_faces(file_bytes: bytes) -> list:
    img_bgr = _bytes_to_bgr(file_bytes)
    if img_bgr is None:
        return []
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_fd = mp.solutions.face_detection
    with mp_fd.FaceDetection(min_detection_confidence=0.5) as detector:
        results = detector.process(img_rgb)
    return results.detections or []


def _extract_landmarks(file_bytes: bytes) -> list[tuple[float, float, float]] | None:
    img_bgr = _bytes_to_bgr(file_bytes)
    if img_bgr is None:
        return None
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mp_fm = mp.solutions.face_mesh
    with mp_fm.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
    ) as face_mesh:
        results = face_mesh.process(img_rgb)
    if not results.multi_face_landmarks:
        return None
    lms = results.multi_face_landmarks[0].landmark
    return [(lm.x, lm.y, lm.z) for lm in lms]


def _cosine_similarity(a: list, b: list) -> float:
    va = np.array(a).flatten()
    vb = np.array(b).flatten()
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def _liveness_score(signals: dict) -> tuple[float, bool]:
    checks = [
        bool(signals.get("blink_detected", False)),
        bool(signals.get("head_pose_changed", False)),
        bool(signals.get("challenge_passed", False)),
    ]
    score = sum(1 for c in checks if c) / len(checks)
    return round(score, 4), score >= _LIVENESS_PASS_THRESHOLD


# ── Service functions ─────────────────────────────────────────────────────────

def register_employee_face(
    db: Session,
    employee_id: int,
    actor_account_id: int,
    file_bytes: bytes,
    filename: str,
    ip_address: str | None,
) -> RegisterFaceData:
    if get_employee_by_id(db, employee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
        )

    if len(file_bytes) > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "Image must be ≤ 5 MB", "details": {}},
        )

    pil_img = _load_pil_image(file_bytes)

    w, h = pil_img.size
    if w < _MIN_IMAGE_DIMENSION or h < _MIN_IMAGE_DIMENSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "IMAGE_TOO_SMALL", "message": "Image resolution is too low for reliable match", "details": {}},
        )

    detections = _detect_faces(file_bytes)
    if len(detections) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NO_FACE_DETECTED", "message": "No face was detected in the uploaded image", "details": {}},
        )
    if len(detections) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MULTIPLE_FACES", "message": "More than one face detected in the image", "details": {}},
        )

    # delete previous object from storage if one exists
    existing = get_face_reference(db, employee_id)
    if existing:
        storage.delete_file(existing.face_object_key)

    ext = "jpg" if pil_img.format == "JPEG" else "png"
    today = date.today().isoformat()
    object_key = f"faces/employee_{employee_id}/reference_{today}.{ext}"
    content_type = "image/jpeg" if ext == "jpg" else "image/png"
    storage.upload_file(object_key, file_bytes, content_type)

    ref = upsert_face_reference(db, employee_id, object_key)

    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.update,
        target_entity="EMPLOYEE",
        target_id=employee_id,
        ip_address=ip_address,
    )

    return RegisterFaceData(
        employee_id=employee_id,
        face_registered=True,
        face_object_key=ref.face_object_key,
        registered_at=ref.registered_at,
    )


def get_face_status(db: Session, employee_id: int) -> FaceStatusData:
    if get_employee_by_id(db, employee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
        )

    ref = get_face_reference(db, employee_id)
    return FaceStatusData(
        employee_id=employee_id,
        face_registered=ref is not None,
        face_object_key=ref.face_object_key if ref else None,
        registered_at=ref.registered_at if ref else None,
    )


def remove_employee_face(
    db: Session,
    employee_id: int,
    actor_account_id: int,
    ip_address: str | None,
) -> DeleteFaceData:
    if get_employee_by_id(db, employee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMPLOYEE_NOT_FOUND", "message": "Employee not found", "details": {}},
        )

    ref = get_face_reference(db, employee_id)
    if ref is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FACE_NOT_REGISTERED", "message": "Employee has no face on record", "details": {}},
        )

    storage.delete_file(ref.face_object_key)
    delete_face_reference(db, employee_id)

    create_audit_log(
        db,
        account_id=actor_account_id,
        action_type=AuditActionType.update,
        target_entity="EMPLOYEE",
        target_id=employee_id,
        ip_address=ip_address,
    )

    return DeleteFaceData(employee_id=employee_id, face_removed=True)


def verify_face_internal(
    db: Session,
    employee_id: int,
    selfie_bytes: bytes,
    liveness_signals_raw: str,
) -> VerifyFaceData:
    ref = get_face_reference(db, employee_id)
    if ref is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FACE_NOT_REGISTERED", "message": "Employee has no face on record", "details": {}},
        )

    try:
        liveness_signals = json.loads(liveness_signals_raw)
    except (json.JSONDecodeError, TypeError):
        liveness_signals = {}

    reference_bytes = storage.download_file(ref.face_object_key)

    ref_landmarks = _extract_landmarks(reference_bytes)
    selfie_landmarks = _extract_landmarks(selfie_bytes)

    if ref_landmarks is None or selfie_landmarks is None:
        face_match_score = 0.0
        face_matched = False
    else:
        raw_score = _cosine_similarity(ref_landmarks, selfie_landmarks)
        face_match_score = round(max(0.0, min(1.0, raw_score)), 4)
        face_matched = face_match_score >= _FACE_MATCH_THRESHOLD

    liveness_score, liveness_passed = _liveness_score(liveness_signals)

    return VerifyFaceData(
        face_match_score=face_match_score,
        liveness_score=liveness_score,
        face_matched=face_matched,
        liveness_passed=liveness_passed,
    )
