from __future__ import annotations

import math

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentAccount, DbSession
from app.models.business import NotificationType
from app.schemas.common import SuccessResponse
from app.schemas.notification import (
    MarkAllReadData,
    MarkReadData,
    NotificationItem,
    NotificationPreferenceData,
    SendNotificationData,
    SendNotificationRequest,
    UpdatePreferencesData,
    UpdatePreferencesRequest,
)
from app.services import notification_service

notification_router = APIRouter()
internal_notification_router = APIRouter()


# ── Static routes registered before parametric ───────────────────────────────

@notification_router.put(
    "/read-all",
    response_model=SuccessResponse[MarkAllReadData],
)
def mark_all_read(
    account: CurrentAccount,
    db: DbSession,
):
    result = notification_service.mark_all_notifications_read(db=db, account_id=account.account_id)
    return SuccessResponse(data=result)


@notification_router.get(
    "/preferences",
    response_model=SuccessResponse[NotificationPreferenceData],
)
def get_preferences(
    account: CurrentAccount,
    db: DbSession,
):
    result = notification_service.get_preferences(db=db, account_id=account.account_id)
    return SuccessResponse(data=result)


@notification_router.put(
    "/preferences",
    response_model=SuccessResponse[UpdatePreferencesData],
)
def update_preferences(
    payload: UpdatePreferencesRequest,
    account: CurrentAccount,
    db: DbSession,
):
    result = notification_service.update_notification_preferences(
        db=db, account_id=account.account_id, data=payload
    )
    return SuccessResponse(data=result)


# ── Paginated list ────────────────────────────────────────────────────────────

@notification_router.get(
    "",
    response_model=SuccessResponse[list[NotificationItem]],
)
def list_notifications(
    account: CurrentAccount,
    db: DbSession,
    is_read: bool | None = None,
    type: NotificationType | None = None,
    page: int = 1,
    limit: int = Query(default=20, le=100),
):
    items, total, unread_count = notification_service.list_notifications(
        db,
        account_id=account.account_id,
        is_read=is_read,
        type_=type,
        page=page,
        limit=limit,
    )
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    return SuccessResponse(
        data=items,
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "unread_count": unread_count,
        },
    )


# ── Parametric route last ─────────────────────────────────────────────────────

@notification_router.put(
    "/{notification_id}/read",
    response_model=SuccessResponse[MarkReadData],
)
def mark_read(
    notification_id: int,
    account: CurrentAccount,
    db: DbSession,
):
    result = notification_service.mark_read(
        db=db, notification_id=notification_id, account_id=account.account_id
    )
    return SuccessResponse(data=result)


# ── Internal ──────────────────────────────────────────────────────────────────

@internal_notification_router.post(
    "/notifications/send",
    response_model=SuccessResponse[SendNotificationData],
)
def send_notification(
    payload: SendNotificationRequest,
    db: DbSession,
):
    result = notification_service.send_notifications(db=db, payload=payload)
    return SuccessResponse(data=result)
