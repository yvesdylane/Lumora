from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def createAccessToken(data: dict, expiresDelta: timedelta | None = None) -> str:
    toEncode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expiresDelta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    toEncode.update({"exp": expire, "type": "access"})
    return jwt.encode(toEncode, SECRET_KEY, algorithm=ALGORITHM)


def createRefreshToken(data: dict) -> str:
    toEncode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    toEncode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(toEncode, SECRET_KEY, algorithm=ALGORITHM)


def decodeToken(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
