from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashedPassword: Mapped[str] = mapped_column("hashed_password", String, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", server_default=func.now(), nullable=False
    )
