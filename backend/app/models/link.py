# backend/app/models/link.py
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base
# Use forward reference for Note type hint
# from .note import Note

class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL PK

    # Foreign keys referencing the notes table for source and target notes
    source_note_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"), # Match SQL ON DELETE CASCADE
        nullable=False,
        index=True # Match SQL index
    )
    target_note_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"), # Match SQL ON DELETE CASCADE
        nullable=False,
        index=True # Match SQL index
    )

    # Optional field for link type
    link_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Optional[str] maps to nullable=True

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # --- Relationships ---
    # Many-to-One relationship linking back to the source Note
    source_note: Mapped["Note"] = relationship(
        "Note",
        foreign_keys=[source_note_id], # Explicitly specify the foreign key
        back_populates="source_links"
    )

    # Many-to-One relationship linking back to the target Note
    target_note: Mapped["Note"] = relationship(
        "Note",
        foreign_keys=[target_note_id], # Explicitly specify the foreign key
        back_populates="target_links"
    )

    # Define table-level constraints using __table_args__
    __table_args__ = (
        # Ensure a note cannot link to itself
        CheckConstraint('source_note_id <> target_note_id', name='ck_links_no_self_referencing'),
        # Prevent duplicate links between the same two notes (in the same direction)
        UniqueConstraint('source_note_id', 'target_note_id', name='uq_links_source_target'),
        {}, # Extra arguments dictionary
    )

    def __repr__(self):
        return f"<Link(id={self.id}, from={self.source_note_id}, to={self.target_note_id})>"
