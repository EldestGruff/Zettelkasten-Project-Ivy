# backend/app/models/tag.py
from typing import List, Optional

from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base
# Use forward reference for Note type hint
# from .note import Note # Avoid direct import if Note also imports Tag

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True) # SERIAL translates to Integer PK

    # Ensure tag names are unique in the database
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    # --- Relationships ---
    # Many-to-Many relationship with Note via NoteTag association
    # `back_populates` links this side to the `tags` attribute on the Note model
    notes: Mapped[List["Note"]] = relationship(
        "Note", # Forward reference using string
        secondary="note_tags", # Name of the association table
        back_populates="tags"
        # Cascade behavior is often defined primarily on the 'parent' side (Note)
        # but can be added here if specific behavior is needed when a Tag is deleted.
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name!r})>"
