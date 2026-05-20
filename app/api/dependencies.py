from __future__ import annotations

import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token, is_blacklisted
from app.models.business import Account, AccountRole
from app.repositories.auth_repository import get_account_by_id


load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{os.getenv('API_V1_PREFIX', '/api/v1')}/auth/login",
)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_account(
    db: DbSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Account:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHORIZED", "message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except JWTError:
        raise credentials_exc

    if payload.get("type") != "access":
        raise credentials_exc

    jti = payload.get("jti")
    if jti and is_blacklisted(jti):
        raise credentials_exc

    account_id = payload.get("sub")
    if account_id is None:
        raise credentials_exc

    account = get_account_by_id(db, int(account_id))
    if account is None:
        raise credentials_exc

    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ACCOUNT_LOCKED", "message": "Account is locked"},
        )

    return account


CurrentAccount = Annotated[Account, Depends(get_current_account)]


def _role_guard(*roles: AccountRole):
    def dependency(account: CurrentAccount) -> Account:
        if account.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Insufficient permissions"},
            )
        return account
    return dependency


EmployeeAccount = Annotated[Account, Depends(_role_guard(AccountRole.employee))]

HROrAdminAccount = Annotated[
    Account,
    Depends(_role_guard(AccountRole.hr, AccountRole.admin)),
]

ManagerOrAboveAccount = Annotated[
    Account,
    Depends(_role_guard(AccountRole.manager, AccountRole.hr, AccountRole.admin)),
]

AdminAccount = Annotated[Account, Depends(_role_guard(AccountRole.admin))]
