from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import (
    blacklist_jti,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_access_token_expire_minutes,
    get_password_hash,
    is_blacklisted,
    verify_password,
)
from app.models.business import Account, AuditActionType
from app.repositories.auth_repository import (
    create_audit_log,
    get_account_by_username,
    update_last_login,
)
from app.schemas.auth import AccountInfo, EmployeeInfo, LoginData, MeData, RefreshData


def login(
    db: Session,
    username: str,
    password: str,
    ip_address: str | None = None,
) -> LoginData:
    account = get_account_by_username(db, username)

    if account is None or not verify_password(password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid username or password"},
        )

    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ACCOUNT_LOCKED", "message": "Account is locked"},
        )

    now = datetime.now(timezone.utc)
    update_last_login(db, account.account_id, now)

    token_data = {"sub": str(account.account_id), "role": account.role.value}
    access_token, _ = create_access_token(token_data)
    refresh_token, _ = create_refresh_token(token_data)

    create_audit_log(
        db,
        account_id=account.account_id,
        action_type=AuditActionType.login,
        target_entity="ACCOUNT",
        target_id=account.account_id,
        ip_address=ip_address,
    )

    account.last_login_at = now

    return LoginData(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=get_access_token_expire_minutes() * 60,
        account=AccountInfo.model_validate(account),
        employee=EmployeeInfo.model_validate(account.employee),
    )


def refresh_access_token(db: Session, refresh_token_str: str) -> RefreshData:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "INVALID_REFRESH_TOKEN", "message": "Invalid or expired refresh token"},
    )

    try:
        payload = decode_token(refresh_token_str)
    except JWTError:
        raise credentials_exc

    if payload.get("type") != "refresh":
        raise credentials_exc

    jti = payload.get("jti")
    if jti and is_blacklisted(jti):
        raise credentials_exc

    account_id = payload.get("sub")
    if account_id is None:
        raise credentials_exc

    from app.repositories.auth_repository import get_account_by_id
    account = get_account_by_id(db, int(account_id))
    if account is None or not account.is_active:
        raise credentials_exc

    token_data = {"sub": str(account.account_id), "role": account.role.value}
    access_token, _ = create_access_token(token_data)

    return RefreshData(
        access_token=access_token,
        expires_in=get_access_token_expire_minutes() * 60,
    )


def get_me(account: Account) -> MeData:
    return MeData(
        account=AccountInfo.model_validate(account),
        employee=EmployeeInfo.model_validate(account.employee),
    )


def logout(
    db: Session,
    account: Account,
    access_jti: str,
    access_exp: float,
    refresh_token_str: str | None,
    ip_address: str | None = None,
) -> None:
    blacklist_jti(access_jti, access_exp)

    if refresh_token_str:
        try:
            payload = decode_token(refresh_token_str)
            ref_jti = payload.get("jti")
            ref_exp = payload.get("exp")
            if ref_jti and ref_exp:
                blacklist_jti(ref_jti, float(ref_exp))
        except JWTError:
            pass  # already invalid — nothing to revoke

    create_audit_log(
        db,
        account_id=account.account_id,
        action_type=AuditActionType.logout,
        target_entity="ACCOUNT",
        target_id=account.account_id,
        ip_address=ip_address,
    )


def change_password(
    db: Session,
    account: Account,
    current_password: str,
    new_password: str,
    confirm_password: str,
    ip_address: str | None = None,
) -> None:
    if not verify_password(current_password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "WRONG_CURRENT_PASSWORD", "message": "Current password is incorrect"},
        )

    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PASSWORD_MISMATCH", "message": "New password and confirmation do not match"},
        )

    account.password_hash = get_password_hash(new_password)
    db.add(account)
    db.commit()

    create_audit_log(
        db,
        account_id=account.account_id,
        action_type=AuditActionType.update,
        target_entity="ACCOUNT",
        target_id=account.account_id,
        ip_address=ip_address,
    )
