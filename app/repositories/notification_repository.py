from __future__ import annotations

from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.business import (
    Account,
    Notification,
    NotificationPreference,
    NotificationType,
)


def get_notifications(
    db: Session,
    account_id: int,
    *,
    is_read: bool | None = None,
    type_: NotificationType | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Notification]:
    q = db.query(Notification).filter(Notification.account_id == account_id)
    if is_read is not None:
        q = q.filter(Notification.is_read == is_read)
    if type_ is not None:
        q = q.filter(Notification.type == type_)
    return q.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


def count_notifications(
    db: Session,
    account_id: int,
    *,
    is_read: bool | None = None,
    type_: NotificationType | None = None,
) -> int:
    q = db.query(Notification).filter(Notification.account_id == account_id)
    if is_read is not None:
        q = q.filter(Notification.is_read == is_read)
    if type_ is not None:
        q = q.filter(Notification.type == type_)
    return q.count()


def count_unread(db: Session, account_id: int) -> int:
    return (
        db.query(Notification)
        .filter(Notification.account_id == account_id, Notification.is_read == False)  # noqa: E712
        .count()
    )


def get_notification_by_id(db: Session, notification_id: int) -> Notification | None:
    return db.query(Notification).filter(Notification.notification_id == notification_id).first()


def mark_notification_read(db: Session, notification_id: int) -> Notification | None:
    notif = get_notification_by_id(db, notification_id)
    if notif is None:
        return None
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


def mark_all_read(db: Session, account_id: int) -> int:
    result = (
        db.execute(
            update(Notification)
            .where(Notification.account_id == account_id, Notification.is_read == False)  # noqa: E712
            .values(is_read=True)
        )
    )
    db.commit()
    return result.rowcount


def get_or_create_preferences(db: Session, account_id: int) -> NotificationPreference:
    pref = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.account_id == account_id)
        .first()
    )
    if pref is None:
        pref = NotificationPreference(account_id=account_id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def update_preferences(
    db: Session,
    account_id: int,
    *,
    push_enabled: bool,
    in_app_enabled: bool,
    notify_checkin_approved: bool,
    notify_checkin_rejected: bool,
    notify_checkout_approved: bool,
    notify_checkout_rejected: bool,
    notify_device_trusted: bool,
    notify_exception_flagged: bool,
) -> NotificationPreference:
    pref = get_or_create_preferences(db, account_id)
    pref.push_enabled = push_enabled
    pref.in_app_enabled = in_app_enabled
    pref.notify_checkin_approved = notify_checkin_approved
    pref.notify_checkin_rejected = notify_checkin_rejected
    pref.notify_checkout_approved = notify_checkout_approved
    pref.notify_checkout_rejected = notify_checkout_rejected
    pref.notify_device_trusted = notify_device_trusted
    pref.notify_exception_flagged = notify_exception_flagged
    db.commit()
    db.refresh(pref)
    return pref


def get_account_by_id_simple(db: Session, account_id: int) -> Account | None:
    return db.query(Account).filter(Account.account_id == account_id).first()


def create_notification(
    db: Session,
    *,
    account_id: int,
    type_: NotificationType,
    title: str,
    body: str,
    meta: dict[str, Any] | None,
) -> Notification:
    notif = Notification(
        account_id=account_id,
        type=type_,
        title=title,
        body=body,
        meta=meta,
    )
    db.add(notif)
    return notif
