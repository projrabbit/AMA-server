from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.models.business import (
    Account,
    AccountRole,
    AuditActionType,
    AuditLog,
    Department,
    Employee,
)


def get_account_by_username(db: Session, username: str) -> Account | None:
    return (
        db.query(Account)
        .options(joinedload(Account.employee))
        .filter(Account.username == username)
        .first()
    )


def get_account_by_id(db: Session, account_id: int) -> Account | None:
    return (
        db.query(Account)
        .options(joinedload(Account.employee))
        .filter(Account.account_id == account_id)
        .first()
    )


def update_last_login(db: Session, account_id: int, dt: datetime) -> None:
    db.execute(
        update(Account)
        .where(Account.account_id == account_id)
        .values(last_login_at=dt)
    )
    db.commit()


def get_employee_by_email(db: Session, email: str) -> Employee | None:
    return db.execute(
        select(Employee).where(Employee.email == email)
    ).scalars().first()


def get_or_create_department(db: Session, name: str) -> Department:
    dept = db.execute(
        select(Department).where(Department.name == name)
    ).scalars().first()
    if dept is not None:
        return dept
    dept = Department(name=name, description=f"Auto-created department: {name}")
    db.add(dept)
    db.flush()
    return dept


def create_employee_and_account(
    db: Session,
    *,
    username: str,
    password_hash: str,
    full_name: str,
    email: str,
    role: AccountRole,
    department_name: str,
) -> Account:
    dept = get_or_create_department(db, department_name)
    employee = Employee(
        department_id=dept.department_id,
        full_name=full_name,
        email=email,
    )
    db.add(employee)
    db.flush()

    account = Account(
        employee_id=employee.employee_id,
        username=username,
        password_hash=password_hash,
        role=role,
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def create_audit_log(
    db: Session,
    account_id: int,
    action_type: AuditActionType,
    target_entity: str,
    target_id: int | None = None,
    payload: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    log = AuditLog(
        account_id=account_id,
        action_type=action_type,
        target_entity=target_entity,
        target_id=target_id,
        payload=payload,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
