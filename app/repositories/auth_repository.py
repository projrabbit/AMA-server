from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session, joinedload

from app.models.business import Account, AuditLog, AuditActionType


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
