# backend/app/models/note.py
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base
from .enums import MemoryTypeEnum # Make sure this is your Python Enum

class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[MemoryTypeEnum] = mapped_column(
        Enum(MemoryTypeEnum, name="memory_type_enum", create_type=True), # This created the type initially
        nullable=False,
        default=MemoryTypeEnum.uncategorized,
        index=True
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    # --- NEW: Columns for storing AI's last suggestion ---
    ai_suggested_memory_type: Mapped[Optional[MemoryTypeEnum]] = mapped_column(
        Enum(MemoryTypeEnum, name="memory_type_enum", create_type=False), # Use existing enum
        nullable=True,
        index=True # Optional: index if you might query by it
    )
    ai_suggestion_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships ---
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary="note_tags",
        back_populates="notes",
        cascade="all, delete"
    )
    source_links: Mapped[List["Link"]] = relationship(
        "Link",
        foreign_keys="Link.source_note_id",
        back_populates="source_note",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    target_links: Mapped[List["Link"]] = relationship(
        "Link",
        foreign_keys="Link.target_note_id",
        back_populates="target_note",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Note(id={self.id!r}, type={self.memory_type.name}, archived={self.is_archived})>"