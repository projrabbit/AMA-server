from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from app.core.config import settings


ALGORITHM = "HS256"
_HASH_NAME = "sha256"
_HASH_ITERATIONS = 600_000
_SALT_BYTES = 16


def get_password_hash(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    key = hashlib.pbkdf2_hmac(
        _HASH_NAME,
        password.encode("utf-8"),
        salt,
        _HASH_ITERATIONS,
    )
    return "$".join(
        [
            f"pbkdf2_{_HASH_NAME}",
            str(_HASH_ITERATIONS),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(key).decode("ascii"),
        ]
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations, salt, key = hashed_password.split("$", 3)
        if algorithm != f"pbkdf2_{_HASH_NAME}":
            return False

        expected_key = base64.b64decode(key.encode("ascii"))
        new_key = hashlib.pbkdf2_hmac(
            _HASH_NAME,
            plain_password.encode("utf-8"),
            base64.b64decode(salt.encode("ascii")),
            int(iterations),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(new_key, expected_key)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
