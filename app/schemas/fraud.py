from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class LivenessSignals(BaseModel):
    blink_detected: bool = False
    head_pose_changed: bool = False
    challenge_passed: bool = False


class RawSignals(BaseModel):
    provider: str | None = None
    speed_mps: float | None = None
    bearing: float | None = None


class EvaluateFraudRequest(BaseModel):
    employee_id: int
    device_fingerprint: str
    latitude: float
    longitude: float
    altitude: float | None = None
    gps_accuracy: float | None = None
    timestamp: datetime
    is_mock_location: bool = False
    face_image_object_key: str | None = None
    liveness_signals: LivenessSignals = LivenessSignals()
    raw_signals: RawSignals | None = None


class EvaluateFraudResult(BaseModel):
    mock_location_detected: bool
    gps_spoofing_detected: bool
    buddy_punch_suspected: bool
    unknown_device: bool
    face_mismatch_detected: bool
    liveness_failed: bool
    confidence_score: float
    reason: str | None
    flags: list[str]


class FraudEmployeeInfo(BaseModel):
    employee_id: int
    full_name: str
    department_name: str | None


class FraudRecordItem(BaseModel):
    fraud_id: int
    record_id: int
    employee: FraudEmployeeInfo
    attendance_type: str
    attendance_timestamp: datetime
    mock_location_detected: bool
    gps_spoofing_detected: bool
    buddy_punch_suspected: bool
    unknown_device: bool
    face_mismatch_detected: bool
    liveness_failed: bool
    confidence_score: float | None
    reason: str | None
    checked_at: datetime


class FraudAttendanceInfo(BaseModel):
    type: str
    timestamp: datetime
    status: str
    rejection_reason: str | None
    latitude: Decimal
    longitude: Decimal
    altitude: Decimal | None
    gps_accuracy: Decimal | None


class FraudDeviceInfo(BaseModel):
    device_id: int
    device_fingerprint: str
    platform: str
    model: str | None
    is_trusted: bool


class FraudRecordDetailData(BaseModel):
    fraud_id: int
    record_id: int
    employee: FraudEmployeeInfo
    attendance: FraudAttendanceInfo
    device: FraudDeviceInfo
    mock_location_detected: bool
    gps_spoofing_detected: bool
    buddy_punch_suspected: bool
    unknown_device: bool
    face_mismatch_detected: bool
    liveness_failed: bool
    confidence_score: float | None
    reason: str | None
    checked_at: datetime
