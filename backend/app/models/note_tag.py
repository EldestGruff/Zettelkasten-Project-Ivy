# backend/app/models/note_tag.py
import uuid
from sqlalchemy import Column, Integer, ForeignKey, PrimaryKeyConstraint, Uuid

from .base import Base

class NoteTag(Base):
    __tablename__ = "note_tags"

    # Define columns as foreign keys to the notes and tags tables
    note_id: uuid.UUID = Column(Uuid(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    tag_id: int = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    # Define the composite primary key using __table_args__
    __table_args__ = (
        PrimaryKeyConstraint('note_id', 'tag_id'),
        {}, # Extra arguments dictionary (can be empty)
    )

    def __repr__(self):
        return f"<NoteTag(note_id={self.note_id}, tag_id={self.tag_id})>"
