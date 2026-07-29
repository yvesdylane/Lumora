from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.timeline.models import ProjectRow  # noqa: F401 — ensure table is registered for FK resolution


class AssetRow(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False, index=True)
    duration: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    b2_key: Mapped[str | None] = mapped_column(String(1023), nullable=True)
    local_path: Mapped[str | None] = mapped_column(String(1023), nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manifest_ref: Mapped[str | None] = mapped_column(String(1023), nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
