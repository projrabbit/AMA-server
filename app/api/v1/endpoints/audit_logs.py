from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from app.api.dependencies import DbSession, HROrAdminAccount
from app.models.business import AuditActionType
from app.schemas.audit import AuditLogItem, AuditLogListData
from app.schemas.common import SuccessResponse
from app.services import audit_service

router = APIRouter()


@router.get("/")
def list_audit_logs(
    account: HROrAdminAccount,
    db: DbSession,
    account_id: int | None = None,
    action_type: AuditActionType | None = None,
    target_entity: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SuccessResponse[AuditLogListData]:
    data = audit_service.list_audit_logs_svc(
        db,
        account_id=account_id,
        action_type=action_type,
        target_entity=target_entity,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    return SuccessResponse(data=data)


@router.get("/{log_id}")
def get_audit_log(
    log_id: int,
    account: HROrAdminAccount,
    db: DbSession,
) -> SuccessResponse[AuditLogItem]:
    data = audit_service.get_audit_log_svc(db, log_id)
    return SuccessResponse(data=data)
