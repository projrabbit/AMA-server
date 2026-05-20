from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from dotenv import load_dotenv
from jose import jwt


load_dotenv()

ALGORITHM = "HS256"
_HASH_NAME = "sha256"
_HASH_ITERATIONS = 600_000
_SALT_BYTES = 16

# jti → expiry unix timestamp; pruned on every read
_token_blacklist: dict[str, float] = {}


def get_secret_key() -> str:
    return os.getenv("SECRET_KEY", "change-this-secret-key")


def get_access_token_expire_minutes() -> int:
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


def get_refresh_token_expire_days() -> int:
    return int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


# ---------- password ----------

def get_password_hash(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    key = hashlib.pbkdf2_hmac(_HASH_NAME, password.encode(), salt, _HASH_ITERATIONS)
    return "$".join([
        f"pbkdf2_{_HASH_NAME}",
        str(_HASH_ITERATIONS),
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(key).decode("ascii"),
    ])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations, salt_b64, key_b64 = hashed_password.split("$", 3)
        if algorithm != f"pbkdf2_{_HASH_NAME}":
            return False
        expected = base64.b64decode(key_b64)
        new_key = hashlib.pbkdf2_hmac(
            _HASH_NAME,
            plain_password.encode(),
            base64.b64decode(salt_b64),
            int(iterations),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(new_key, expected)


# ---------- tokens ----------

def _build_token(
    data: dict[str, Any],
    token_type: str,
    expires_delta: timedelta,
) -> tuple[str, str]:
    """Return (encoded_jwt, jti)."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {**data, "type": token_type, "jti": jti, "exp": expire}
    return jwt.encode(payload, get_secret_key(), algorithm=ALGORITHM), jti


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    delta = expires_delta or timedelta(minutes=get_access_token_expire_minutes())
    return _build_token(data, "access", delta)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    delta = expires_delta or timedelta(days=get_refresh_token_expire_days())
    return _build_token(data, "refresh", delta)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and return the JWT payload. Raises JWTError on failure."""
    return jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])


# ---------- blacklist ----------

def _prune_blacklist() -> None:
    now = time.time()
    expired = [jti for jti, exp in _token_blacklist.items() if exp <= now]
    for jti in expired:
        del _token_blacklist[jti]


def blacklist_jti(jti: str, expiry_ts: float) -> None:
    _token_blacklist[jti] = expiry_ts
    _prune_blacklist()


def is_blacklisted(jti: str) -> bool:
    _prune_blacklist()
    return jti in _token_blacklist
