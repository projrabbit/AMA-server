from __future__ import annotations

import math
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.business import NotificationType
from app.repositories.notification_repository import (
    count_notifications,
    count_unread,
    create_notification,
    get_account_by_id_simple,
    get_notification_by_id,
    get_notifications,
    get_or_create_preferences,
    mark_all_read,
    mark_notification_read,
    update_preferences,
)
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


def list_notifications(
    db: Session,
    account_id: int,
    *,
    is_read: bool | None = None,
    type_: NotificationType | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[NotificationItem], int, int]:
    skip = (page - 1) * limit
    rows = get_notifications(db, account_id, is_read=is_read, type_=type_, skip=skip, limit=limit)
    total = count_notifications(db, account_id, is_read=is_read, type_=type_)
    unread_count = count_unread(db, account_id)

    items = [
        NotificationItem(
            notification_id=n.notification_id,
            type=n.type.value if hasattr(n.type, "value") else str(n.type),
            title=n.title,
            body=n.body,
            is_read=n.is_read,
            created_at=n.created_at,
            meta=n.meta,
        )
        for n in rows
    ]
    return items, total, unread_count


def mark_read(db: Session, notification_id: int, account_id: int) -> MarkReadData:
    notif = get_notification_by_id(db, notification_id)
    if notif is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notification not found", "details": {}},
        )
    if notif.account_id != account_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Notification belongs to a different account", "details": {}},
        )
    updated = mark_notification_read(db, notification_id)
    return MarkReadData(notification_id=updated.notification_id, is_read=updated.is_read)


def mark_all_notifications_read(db: Session, account_id: int) -> MarkAllReadData:
    count = mark_all_read(db, account_id)
    return MarkAllReadData(marked_count=count)


def get_preferences(db: Session, account_id: int) -> NotificationPreferenceData:
    pref = get_or_create_preferences(db, account_id)
    return NotificationPreferenceData(
        account_id=pref.account_id,
        push_enabled=pref.push_enabled,
        in_app_enabled=pref.in_app_enabled,
        notify_checkin_approved=pref.notify_checkin_approved,
        notify_checkin_rejected=pref.notify_checkin_rejected,
        notify_checkout_approved=pref.notify_checkout_approved,
        notify_checkout_rejected=pref.notify_checkout_rejected,
        notify_device_trusted=pref.notify_device_trusted,
        notify_exception_flagged=pref.notify_exception_flagged,
    )


def update_notification_preferences(
    db: Session,
    account_id: int,
    data: UpdatePreferencesRequest,
) -> UpdatePreferencesData:
    update_preferences(
        db,
        account_id,
        push_enabled=data.push_enabled,
        in_app_enabled=data.in_app_enabled,
        notify_checkin_approved=data.notify_checkin_approved,
        notify_checkin_rejected=data.notify_checkin_rejected,
        notify_checkout_approved=data.notify_checkout_approved,
        notify_checkout_rejected=data.notify_checkout_rejected,
        notify_device_trusted=data.notify_device_trusted,
        notify_exception_flagged=data.notify_exception_flagged,
    )
    return UpdatePreferencesData(updated=True)


def send_notifications(db: Session, payload: SendNotificationRequest) -> SendNotificationData:
    sent = 0
    failed = 0
    for account_id in payload.account_ids:
        account = get_account_by_id_simple(db, account_id)
        if account is None:
            failed += 1
            continue
        create_notification(
            db,
            account_id=account_id,
            type_=payload.type,
            title=payload.title,
            body=payload.body,
            meta=payload.meta,
        )
        sent += 1
    if sent > 0:
        db.commit()
    return SendNotificationData(sent_count=sent, failed_count=failed)
