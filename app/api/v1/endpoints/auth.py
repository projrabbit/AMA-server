from __future__ import annotations

from fastapi import APIRouter, Request, status
from jose import JWTError

from app.api.dependencies import CurrentAccount, DbSession
from app.core.security import decode_token
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginData,
    MeData,
    MessageData,
    RefreshData,
    RefreshTokenRequest,
)
from app.schemas.common import SuccessResponse
from app.services import auth_service


router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post(
    "/login",
    response_model=SuccessResponse[LoginData],
    status_code=status.HTTP_200_OK,
    summary="Login",
    description="Authenticate with username and password. Returns access and refresh tokens.",
)
def login(
    body: LoginRequest,
    request: Request,
    db: DbSession,
) -> SuccessResponse[LoginData]:
    data = auth_service.login(db, body.username, body.password, _client_ip(request))
    return SuccessResponse(data=data)


@router.post(
    "/refresh",
    response_model=SuccessResponse[RefreshData],
    status_code=status.HTTP_200_OK,
    summary="Refresh Token",
    description="Issue a new access token using a valid refresh token.",
)
def refresh_token(
    body: RefreshTokenRequest,
    db: DbSession,
) -> SuccessResponse[RefreshData]:
    data = auth_service.refresh_access_token(db, body.refresh_token)
    return SuccessResponse(data=data)


@router.get(
    "/me",
    response_model=SuccessResponse[MeData],
    status_code=status.HTTP_200_OK,
    summary="Current User",
    description="Return the authenticated user's account and employee profile.",
)
def me(account: CurrentAccount) -> SuccessResponse[MeData]:
    return SuccessResponse(data=auth_service.get_me(account))


@router.post(
    "/logout",
    response_model=SuccessResponse[MessageData],
    status_code=status.HTTP_200_OK,
    summary="Logout",
    description="Revoke the current access token and optionally the refresh token.",
)
def logout(
    body: RefreshTokenRequest | None = None,
    *,
    account: CurrentAccount,
    request: Request,
    db: DbSession,
) -> SuccessResponse[MessageData]:
    # Extract jti + exp from the bearer token already validated by the dependency
    raw_token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    try:
        payload = decode_token(raw_token)
        access_jti: str = payload["jti"]
        access_exp: float = float(payload["exp"])
    except (JWTError, KeyError):
        access_jti = ""
        access_exp = 0.0

    refresh_str = body.refresh_token if body else None
    auth_service.logout(db, account, access_jti, access_exp, refresh_str, _client_ip(request))
    return SuccessResponse(data=MessageData(message="Logged out successfully"))


@router.put(
    "/change-password",
    response_model=SuccessResponse[MessageData],
    status_code=status.HTTP_200_OK,
    summary="Change Password",
    description="Change the authenticated user's password.",
)
def change_password(
    body: ChangePasswordRequest,
    request: Request,
    account: CurrentAccount,
    db: DbSession,
) -> SuccessResponse[MessageData]:
    auth_service.change_password(
        db,
        account,
        body.current_password,
        body.new_password,
        body.confirm_password,
        _client_ip(request),
    )
    return SuccessResponse(data=MessageData(message="Password changed successfully"))
