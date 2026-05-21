from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.business import AuditActionType, AuditLog


def list_audit_logs(
    db: Session,
    *,
    account_id: int | None = None,
    action_type: AuditActionType | None = None,
    target_entity: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    base = select(AuditLog)
    if account_id is not None:
        base = base.where(AuditLog.account_id == account_id)
    if action_type is not None:
        base = base.where(AuditLog.action_type == action_type)
    if target_entity is not None:
        base = base.where(AuditLog.target_entity == target_entity)
    if since is not None:
        base = base.where(AuditLog.created_at >= since)
    if until is not None:
        base = base.where(AuditLog.created_at <= until)

    total = db.execute(
        select(func.count()).select_from(base.subquery())
    ).scalar_one()

    rows = list(
        db.execute(
            base.order_by(AuditLog.created_at.desc(), AuditLog.log_id.desc())
            .limit(limit)
            .offset(offset)
        ).scalars().all()
    )
    return rows, total


def get_audit_log_by_id(db: Session, log_id: int) -> AuditLog | None:
    return db.get(AuditLog, log_id)
