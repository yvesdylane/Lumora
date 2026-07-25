from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import UserRow
from auth.utils.tokens import decodeToken
from core.database import getSession

_bearerScheme = HTTPBearer()


async def getCurrentUser(
    credentials: HTTPAuthorizationCredentials = Depends(_bearerScheme),
    session: AsyncSession = Depends(getSession),
) -> UserRow:
    token = credentials.credentials
    payload = decodeToken(token)

    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    userId = payload.get("sub")
    if userId is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    result = await session.execute(select(UserRow).where(UserRow.id == userId))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
