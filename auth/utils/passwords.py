from __future__ import annotations

import bcrypt


def hashPassword(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verifyPassword(plainPassword: str, hashedPassword: str) -> bool:
    return bcrypt.checkpw(
        plainPassword.encode("utf-8"), hashedPassword.encode("utf-8")
    )
