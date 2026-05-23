from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ── Shared sub-models ─────────────────────────────────────────────────────────

class ShiftInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    shift_id: int
    name: str
    start_time: time
    end_time: time


class LocationInfo(BaseModel):
    latitude: Decimal
    longitude: Decimal
    altitude: Decimal | None
    gps_accuracy: Decimal | None
    building_id: int | None
    building_name: str | None
    floor_id: int | None
    floor_name: str | None
    geofence_rule_id: int | None


class FraudResultInfo(BaseModel):
    fraud_id: int
    mock_location_detected: bool
    gps_spoofing_detected: bool
    buddy_punch_suspected: bool
    unknown_device: bool
    face_mismatch_detected: bool
    liveness_failed: bool
    confidence_score: float | None


# ── Check-in / Check-out ──────────────────────────────────────────────────────

class CheckInData(BaseModel):
    record_id: int
    employee_id: int
    type: str
    status: str
    rejection_reason: str | None
    message: str
    timestamp: datetime
    is_late: bool
    is_early_leave: bool
    matched_checkin_record_id: int | None = None
    worked_minutes: int | None = None
    shift: ShiftInfo | None
    location: LocationInfo
    fraud_result: FraudResultInfo


# ── Today status ──────────────────────────────────────────────────────────────

class TodayRecordInfo(BaseModel):
    record_id: int
    timestamp: datetime
    status: str


class TodayStatusData(BaseModel):
    date: date
    employee_id: int
    can_check_in: bool
    can_check_out: bool
    current_shift: ShiftInfo | None
    latest_checkin: TodayRecordInfo | None
    latest_checkout: TodayRecordInfo | None


# ── Attendance history ────────────────────────────────────────────────────────

class HistoryEmployeeInfo(BaseModel):
    employee_id: int
    full_name: str


class HistoryDayCheckin(BaseModel):
    record_id: int
    timestamp: datetime
    status: str
    is_late: bool


class HistoryDayCheckout(BaseModel):
    record_id: int
    timestamp: datetime
    status: str
    is_early_leave: bool


class AttendanceDayRecord(BaseModel):
    date: date
    checkin: HistoryDayCheckin | None
    checkout: HistoryDayCheckout | None
    building_name: str | None
    floor_name: str | None
    worked_minutes: int | None
    status: str


class AttendanceSummary(BaseModel):
    work_days: int
    total_work_minutes: int
    late_count: int
    early_leave_count: int
    rejected_count: int


class AttendanceHistoryData(BaseModel):
    employee: HistoryEmployeeInfo
    range: dict
    summary: AttendanceSummary
    days: list[AttendanceDayRecord]


# ── Exceptions list ───────────────────────────────────────────────────────────

class ExceptionEmployeeInfo(BaseModel):
    employee_id: int
    full_name: str
    department_name: str | None


class ExceptionFraudFlags(BaseModel):
    mock_location_detected: bool
    gps_spoofing_detected: bool
    buddy_punch_suspected: bool
    unknown_device: bool
    face_mismatch_detected: bool
    liveness_failed: bool


class ExceptionItem(BaseModel):
    record_id: int
    employee: ExceptionEmployeeInfo
    type: str
    timestamp: datetime
    status: str
    rejection_reason: str | None
    is_late: bool
    is_early_leave: bool
    fraud_flags: ExceptionFraudFlags | None


# ── Record detail ─────────────────────────────────────────────────────────────

class RecordEmployeeInfo(BaseModel):
    employee_id: int
    full_name: str
    department_id: int | None
    department_name: str | None


class RecordDeviceInfo(BaseModel):
    device_id: int
    device_fingerprint: str
    platform: str
    model: str | None
    is_trusted: bool


class RecordShiftInfo(BaseModel):
    shift_id: int
    name: str
    start_time: time
    end_time: time


class RecordFraudDetection(BaseModel):
    fraud_id: int
    mock_location_detected: bool
    gps_spoofing_detected: bool
    buddy_punch_suspected: bool
    unknown_device: bool
    face_mismatch_detected: bool
    liveness_failed: bool
    reason: str | None
    confidence_score: float | None
    checked_at: datetime


class AttendanceRecordDetailData(BaseModel):
    record_id: int
    employee: RecordEmployeeInfo
    device: RecordDeviceInfo
    shift: RecordShiftInfo | None
    geofence_rule_id: int | None
    type: str
    timestamp: datetime
    latitude: Decimal
    longitude: Decimal
    altitude: Decimal | None
    gps_accuracy: Decimal | None
    status: str
    rejection_reason: str | None
    is_late: bool
    is_early_leave: bool
    fraud_detection: RecordFraudDetection | None


# ── Manual approve ────────────────────────────────────────────────────────────

class ApproveRequest(BaseModel):
    note: str | None = None


class ApproveData(BaseModel):
    record_id: int
    status: str
    rejection_reason: str | None
    approved_by_account_id: int
    approved_at: datetime
