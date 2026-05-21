from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.business import AuditActionType


class AuditLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: int
    account_id: int
    action_type: AuditActionType
    target_entity: str
    target_id: int | None
    payload: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime


class AuditLogListData(BaseModel):
    items: list[AuditLogItem]
    total: int
    limit: int
    offset: int
