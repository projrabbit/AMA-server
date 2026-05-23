from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ActiveLocationItem(BaseModel):
    employee_id: int
    full_name: str
    department_name: str
    latitude: float
    longitude: float
    altitude: float | None
    building_id: int | None
    building_name: str | None
    floor_id: int | None
    floor_name: str | None
    last_checkin_at: datetime


class DashboardSummaryData(BaseModel):
    date: date
    total_employees: int
    checked_in_today: int
    on_time_count: int
    late_count: int
    early_leave_count: int
    absent_count: int
    fraud_alerts_today: int
    on_time_rate: float
    active_locations: list[ActiveLocationItem]


class RealtimeLocationItem(BaseModel):
    employee_id: int
    full_name: str
    department_id: int
    department_name: str
    record_id: int
    latitude: float
    longitude: float
    altitude: float | None
    gps_accuracy: float | None
    building_id: int | None
    building_name: str | None
    floor_id: int | None
    floor_name: str | None
    arcgis_layer_id: str | None
    checked_in_at: datetime


class ReportSummary(BaseModel):
    employee_count: int
    total_work_days: int
    total_work_minutes: int
    late_count: int
    early_leave_count: int
    absent_count: int
    rejected_count: int


class ReportEmployeeSummary(BaseModel):
    employee_id: int
    full_name: str
    department_name: str
    work_days: int
    total_work_minutes: int
    late_count: int
    early_leave_count: int
    absent_count: int
    rejected_count: int


class ReportDayDetail(BaseModel):
    date: date
    employee_id: int
    full_name: str
    department_name: str
    checkin_at: datetime | None
    checkout_at: datetime | None
    worked_minutes: int | None
    is_late: bool
    is_early_leave: bool
    status: str


class AttendanceReportData(BaseModel):
    range: dict[str, str]
    summary: ReportSummary
    employees: list[ReportEmployeeSummary]
    details: list[ReportDayDetail]
