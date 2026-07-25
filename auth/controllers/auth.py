from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import UserRow
from auth.schemas import RegisterRequest, LoginRequest, TokenResponse, User
from auth.utils.passwords import hashPassword, verifyPassword
from auth.utils.tokens import createAccessToken, createRefreshToken, decodeToken


async def register(
    session: AsyncSession, data: RegisterRequest
) -> TokenResponse:
    existing = await session.execute(
        select(UserRow).where(UserRow.email == data.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Email already registered")

    user = UserRow(
        id=uuid.uuid4(),
        email=data.email,
        hashedPassword=hashPassword(data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    accessToken = createAccessToken(data={"sub": str(user.id)})
    refreshToken = createRefreshToken(data={"sub": str(user.id)})

    return TokenResponse(accessToken=accessToken, refreshToken=refreshToken)


async def login(
    session: AsyncSession, data: LoginRequest
) -> TokenResponse:
    result = await session.execute(
        select(UserRow).where(UserRow.email == data.email)
    )
    user = result.scalar_one_or_none()

    if user is None or not verifyPassword(data.password, user.hashedPassword):
        raise ValueError("Invalid email or password")

    accessToken = createAccessToken(data={"sub": str(user.id)})
    refreshToken = createRefreshToken(data={"sub": str(user.id)})

    return TokenResponse(accessToken=accessToken, refreshToken=refreshToken)


async def refreshToken(token: str) -> TokenResponse:
    payload = decodeToken(token)
    if payload is None or payload.get("type") != "refresh":
        raise ValueError("Invalid refresh token")

    userId = payload.get("sub")
    if userId is None:
        raise ValueError("Invalid refresh token")

    accessToken = createAccessToken(data={"sub": userId})
    newRefresh = createRefreshToken(data={"sub": userId})

    return TokenResponse(accessToken=accessToken, refreshToken=newRefresh)


async def getMe(userId: str, session: AsyncSession) -> User:
    result = await session.execute(select(UserRow).where(UserRow.id == userId))
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("User not found")

    return User.model_validate(user)
