from __future__ import annotations

import enum
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    false,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

BUSINESS_SCHEMA = "business"


class EmployeeStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    on_leave = "on_leave"
    terminated = "terminated"


class AccountRole(str, enum.Enum):
    employee = "employee"
    hr = "hr"
    manager = "manager"
    admin = "admin"


class DevicePlatform(str, enum.Enum):
    android = "android"
    ios = "ios"
    web = "web"
    other = "other"


class AttendanceType(str, enum.Enum):
    checkin = "checkin"
    checkout = "checkout"


class AttendanceStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    flagged = "flagged"


class AuditActionType(str, enum.Enum):
    login = "login"
    logout = "logout"
    create = "create"
    update = "update"
    delete = "delete"
    checkin = "checkin"
    checkout = "checkout"
    approve = "approve"
    reject = "reject"


employee_status_enum = SQLEnum(EmployeeStatus, name="employee_status", schema=BUSINESS_SCHEMA)
account_role_enum = SQLEnum(AccountRole, name="account_role", schema=BUSINESS_SCHEMA)
device_platform_enum = SQLEnum(DevicePlatform, name="device_platform", schema=BUSINESS_SCHEMA)
attendance_type_enum = SQLEnum(AttendanceType, name="attendance_type", schema=BUSINESS_SCHEMA)
attendance_status_enum = SQLEnum(AttendanceStatus, name="attendance_status", schema=BUSINESS_SCHEMA)
audit_action_type_enum = SQLEnum(AuditActionType, name="audit_action_type", schema=BUSINESS_SCHEMA)


class Department(Base):
    __tablename__ = "department"
    __table_args__ = (
        Index("ix_business_department_name", "name", unique=True),
        Index("ix_business_department_manager_id", "manager_id"),
        {"schema": BUSINESS_SCHEMA},
    )

    department_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    manager_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            f"{BUSINESS_SCHEMA}.employee.employee_id",
            name="fk_business_department_manager_id_employee",
            ondelete="SET NULL",
            use_alter=True,
        ),
    )

    employees: Mapped[list[Employee]] = relationship(
        back_populates="department",
        foreign_keys="Employee.department_id",
    )
    manager: Mapped[Employee | None] = relationship(
        back_populates="managed_departments",
        foreign_keys=[manager_id],
        post_update=True,
    )


class Employee(Base):
    __tablename__ = "employee"
    __table_args__ = (
        Index("ix_business_employee_department_id", "department_id"),
        Index("ix_business_employee_email", "email", unique=True),
        Index("ix_business_employee_phone", "phone", unique=True),
        Index("ix_business_employee_status", "status"),
        {"schema": BUSINESS_SCHEMA},
    )

    employee_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{BUSINESS_SCHEMA}.department.department_id",
            name="fk_business_employee_department_id_department",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    position: Mapped[str | None] = mapped_column(String(100))
    hire_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[EmployeeStatus] = mapped_column(
        employee_status_enum,
        nullable=False,
        server_default=EmployeeStatus.active.value,
    )

    department: Mapped[Department] = relationship(
        back_populates="employees",
        foreign_keys=[department_id],
    )
    managed_departments: Mapped[list[Department]] = relationship(
        back_populates="manager",
        foreign_keys="Department.manager_id",
    )
    account: Mapped[Account | None] = relationship(back_populates="employee", uselist=False)
    devices: Mapped[list[Device]] = relationship(back_populates="employee")
    shifts: Mapped[list[Shift]] = relationship(back_populates="employee")
    attendance_records: Mapped[list[AttendanceRecord]] = relationship(back_populates="employee")


class Account(Base):
    __tablename__ = "account"
    __table_args__ = (
        Index("ix_business_account_employee_id", "employee_id", unique=True),
        Index("ix_business_account_username", "username", unique=True),
        Index("ix_business_account_role", "role"),
        Index("ix_business_account_is_active", "is_active"),
        {"schema": BUSINESS_SCHEMA},
    )

    account_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{BUSINESS_SCHEMA}.employee.employee_id",
            name="fk_business_account_employee_id_employee",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[AccountRole] = mapped_column(
        account_role_enum,
        nullable=False,
        server_default=AccountRole.employee.value,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())

    employee: Mapped[Employee] = relationship(back_populates="account")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="account")


class Device(Base):
    __tablename__ = "device"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "device_fingerprint",
            name="uq_business_device_employee_fingerprint",
        ),
        Index("ix_business_device_employee_id", "employee_id"),
        Index("ix_business_device_device_fingerprint", "device_fingerprint"),
        Index("ix_business_device_platform", "platform"),
        Index("ix_business_device_is_trusted", "is_trusted"),
        {"schema": BUSINESS_SCHEMA},
    )

    device_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{BUSINESS_SCHEMA}.employee.employee_id",
            name="fk_business_device_employee_id_employee",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    device_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[DevicePlatform] = mapped_column(device_platform_enum, nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(100))
    app_version: Mapped[str | None] = mapped_column(String(50))
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    is_trusted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())

    employee: Mapped[Employee] = relationship(back_populates="devices")
    attendance_records: Mapped[list[AttendanceRecord]] = relationship(back_populates="device")


class Shift(Base):
    __tablename__ = "shift"
    __table_args__ = (
        CheckConstraint(
            "late_tolerance_min >= 0",
            name="ck_business_shift_late_tolerance_min_non_negative",
        ),
        CheckConstraint(
            "early_leave_min >= 0",
            name="ck_business_shift_early_leave_min_non_negative",
        ),
        Index("ix_business_shift_employee_id", "employee_id"),
        Index("ix_business_shift_name", "name"),
        Index("ix_business_shift_start_time_end_time", "start_time", "end_time"),
        {"schema": BUSINESS_SCHEMA},
    )

    shift_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{BUSINESS_SCHEMA}.employee.employee_id",
            name="fk_business_shift_employee_id_employee",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    late_tolerance_min: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    early_leave_min: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    apply_to_weekends: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())

    employee: Mapped[Employee] = relationship(back_populates="shifts")
    attendance_records: Mapped[list[AttendanceRecord]] = relationship(back_populates="shift")


class AttendanceRecord(Base):
    __tablename__ = "attendance_record"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="ck_business_attendance_record_latitude_range",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="ck_business_attendance_record_longitude_range",
        ),
        CheckConstraint(
            "gps_accuracy IS NULL OR gps_accuracy >= 0",
            name="ck_business_attendance_record_gps_accuracy_non_negative",
        ),
        Index("ix_business_attendance_record_employee_id", "employee_id"),
        Index("ix_business_attendance_record_device_id", "device_id"),
        Index("ix_business_attendance_record_shift_id", "shift_id"),
        Index("ix_business_attendance_record_geofence_rule_id", "geofence_rule_id"),
        Index("ix_business_attendance_record_timestamp", "timestamp"),
        Index("ix_business_attendance_record_status", "status"),
        Index("ix_business_attendance_record_type", "type"),
        {"schema": BUSINESS_SCHEMA},
    )

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{BUSINESS_SCHEMA}.employee.employee_id",
            name="fk_business_attendance_record_employee_id_employee",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{BUSINESS_SCHEMA}.device.device_id",
            name="fk_business_attendance_record_device_id_device",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    shift_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{BUSINESS_SCHEMA}.shift.shift_id",
            name="fk_business_attendance_record_shift_id_shift",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    geofence_rule_id: Mapped[int] = mapped_column(
        ForeignKey(
            "gis.geofence_rule.geofence_rule_id",
            name="fk_business_attendance_record_geofence_rule_id_geofence_rule",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    type: Mapped[AttendanceType] = mapped_column(attendance_type_enum, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    altitude: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    gps_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    status: Mapped[AttendanceStatus] = mapped_column(
        attendance_status_enum,
        nullable=False,
        server_default=AttendanceStatus.pending.value,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    is_late: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    is_early_leave: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())

    employee: Mapped[Employee] = relationship(back_populates="attendance_records")
    device: Mapped[Device] = relationship(back_populates="attendance_records")
    shift: Mapped[Shift] = relationship(back_populates="attendance_records")
    geofence_rule: Mapped[GeofenceRule] = relationship(back_populates="attendance_records")
    fraud_detection: Mapped[FraudDetection | None] = relationship(
        back_populates="attendance_record",
        uselist=False,
    )


class FraudDetection(Base):
    __tablename__ = "fraud_detection"
    __table_args__ = (
        Index("ix_business_fraud_detection_record_id", "record_id", unique=True),
        Index("ix_business_fraud_detection_mock_location_detected", "mock_location_detected"),
        Index("ix_business_fraud_detection_gps_spoofing_detected", "gps_spoofing_detected"),
        Index("ix_business_fraud_detection_buddy_punch_suspected", "buddy_punch_suspected"),
        Index("ix_business_fraud_detection_checked_at", "checked_at"),
        {"schema": BUSINESS_SCHEMA},
    )

    fraud_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{BUSINESS_SCHEMA}.attendance_record.record_id",
            name="fk_business_fraud_detection_record_id_attendance_record",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    mock_location_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    gps_spoofing_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    buddy_punch_suspected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    reason: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    attendance_record: Mapped[AttendanceRecord] = relationship(back_populates="fraud_detection")


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_business_audit_log_account_id", "account_id"),
        Index("ix_business_audit_log_action_type", "action_type"),
        Index("ix_business_audit_log_target_entity", "target_entity"),
        Index("ix_business_audit_log_target_id", "target_id"),
        Index("ix_business_audit_log_created_at", "created_at"),
        {"schema": BUSINESS_SCHEMA},
    )

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey(
            f"{BUSINESS_SCHEMA}.account.account_id",
            name="fk_business_audit_log_account_id_account",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    action_type: Mapped[AuditActionType] = mapped_column(audit_action_type_enum, nullable=False)
    target_entity: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    account: Mapped[Account] = relationship(back_populates="audit_logs")
