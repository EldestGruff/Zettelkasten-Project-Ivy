# backend/app/models/note.py
import uuid
from datetime import datetime
from typing import List, Optional # Need Optional for nullable relationships if lazy loading

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func # For default timestamps

from .base import Base
from .enums import MemoryTypeEnum
# We'll have circular dependencies if we import Tag and Link directly here for types
# Use forward references (strings) or handle type hints carefully later if needed.

class Note(Base):
    __tablename__ = "notes" # Explicitly defining table name

    # Use Mapped and mapped_column for modern SQLAlchemy type hinting
    # Use uuid.UUID for the Python type hint
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Use the Python enum directly, SQLAlchemy handles mapping to PG Enum
    memory_type: Mapped[MemoryTypeEnum] = mapped_column(
        Enum(MemoryTypeEnum, name="memory_type_enum", create_type=True),
        nullable=False,
        default=MemoryTypeEnum.uncategorized,
        index=True # Matches index created in SQL
    )

    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True # Matches index
    )

    # Use server_default for database-level default timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # Database trigger handles updates, but good practice to set onupdate as well
    # Note: func.now() might capture transaction start time, CURRENT_TIMESTAMP captures statement time
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships ---
    # Many-to-Many relationship with Tag via NoteTag association object/table
    # `back_populates` links this side of the relationship to the corresponding attribute on the Tag model
    # `cascade` defines what happens when a Note is deleted/modified (matches ON DELETE CASCADE)
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", # Forward reference using string
        secondary="note_tags", # Name of the association table
        back_populates="notes",
        cascade="all, delete" # Matches SQL ON DELETE CASCADE behavior
    )

    # One-to-Many relationship for links originating *from* this note
    source_links: Mapped[List["Link"]] = relationship(
        "Link",
        foreign_keys="Link.source_note_id", # Specify join condition explicitly
        back_populates="source_note",
        cascade="all, delete-orphan",
        lazy="selectin" # Example loading strategy (optional)
    )

    # One-to-Many relationship for links pointing *to* this note
    target_links: Mapped[List["Link"]] = relationship(
        "Link",
        foreign_keys="Link.target_note_id", # Specify join condition explicitly
        back_populates="target_note",
        cascade="all, delete-orphan",
        lazy="selectin" # Example loading strategy (optional)
    )

    def __repr__(self):
        return f"<Note(id={self.id!r}, type={self.memory_type.name}, archived={self.is_archived})>"
