from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status

from app.models.business import AuditActionType
from app.repositories.audit_repository import (
    get_audit_log_by_id,
    list_audit_logs,
)
from app.schemas.audit import AuditLogItem, AuditLogListData


MAX_LIMIT = 100
DEFAULT_LIMIT = 20


def list_audit_logs_svc(
    db,
    *,
    account_id: int | None,
    action_type: AuditActionType | None,
    target_entity: str | None,
    since: datetime | None,
    until: datetime | None,
    limit: int | None,
    offset: int | None,
) -> AuditLogListData:
    eff_limit = min(MAX_LIMIT, max(1, limit if limit is not None else DEFAULT_LIMIT))
    eff_offset = max(0, offset if offset is not None else 0)

    rows, total = list_audit_logs(
        db,
        account_id=account_id,
        action_type=action_type,
        target_entity=target_entity,
        since=since,
        until=until,
        limit=eff_limit,
        offset=eff_offset,
    )
    return AuditLogListData(
        items=[AuditLogItem.model_validate(r) for r in rows],
        total=total,
        limit=eff_limit,
        offset=eff_offset,
    )


def get_audit_log_svc(db, log_id: int) -> AuditLogItem:
    log = get_audit_log_by_id(db, log_id)
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "LOG_NOT_FOUND", "message": "Audit log entry not found", "details": {}},
        )
    return AuditLogItem.model_validate(log)
