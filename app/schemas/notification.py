from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.business import NotificationType


class NotificationItem(BaseModel):
    notification_id: int
    type: str
    title: str
    body: str
    is_read: bool
    created_at: datetime
    meta: dict[str, Any] | None


class MarkReadData(BaseModel):
    notification_id: int
    is_read: bool


class MarkAllReadData(BaseModel):
    marked_count: int


class NotificationPreferenceData(BaseModel):
    account_id: int
    push_enabled: bool
    in_app_enabled: bool
    notify_checkin_approved: bool
    notify_checkin_rejected: bool
    notify_checkout_approved: bool
    notify_checkout_rejected: bool
    notify_device_trusted: bool
    notify_exception_flagged: bool


class UpdatePreferencesRequest(BaseModel):
    push_enabled: bool
    in_app_enabled: bool
    notify_checkin_approved: bool
    notify_checkin_rejected: bool
    notify_checkout_approved: bool
    notify_checkout_rejected: bool
    notify_device_trusted: bool
    notify_exception_flagged: bool


class UpdatePreferencesData(BaseModel):
    updated: bool


class SendNotificationRequest(BaseModel):
    account_ids: list[int]
    type: NotificationType
    title: str
    body: str
    meta: dict[str, Any] | None = None


class SendNotificationData(BaseModel):
    sent_count: int
    failed_count: int
