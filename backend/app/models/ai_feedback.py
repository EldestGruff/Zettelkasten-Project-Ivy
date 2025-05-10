# backend/app/models/ai_feedback.py
import uuid
from datetime import datetime
from typing import Optional

# Import necessary SQLAlchemy components
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Uuid # Ensure all used SQL types are here
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func # For CURRENT_TIMESTAMP equivalent

from .base import Base # Your declarative base
from .enums import MemoryTypeEnum # Your Python enum for memory types

class AICategorizationFeedback(Base): # Inherits from Base
    __tablename__ = "ai_categorization_feedback" # Matches SQL table name

    # id SERIAL PRIMARY KEY
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 'SERIAL' in Postgres implies integer, primary key, and auto-increment.

    # note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE
    # + CREATE INDEX idx_aicf_note_id ON ai_categorization_feedback(note_id);
    note_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), # SQLAlchemy type for UUID
        ForeignKey("notes.id", ondelete="CASCADE"), # Defines foreign key and cascade behavior
        nullable=False, # NOT NULL
        index=True # Corresponds to CREATE INDEX
    )

    # note_content_snippet TEXT
    note_content_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # TEXT maps to Text. Optional[str] means it can be NULL (default for nullable=True).

    # prompt_used TEXT
    prompt_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ai_suggested_type memory_type_enum
    # + CREATE INDEX idx_aicf_ai_suggested_type ON ai_categorization_feedback(ai_suggested_type);
    ai_suggested_type: Mapped[Optional[MemoryTypeEnum]] = mapped_column(
        Enum(MemoryTypeEnum, name="memory_type_enum", create_type=False),
        # 'Enum' maps to PostgreSQL ENUM.
        # 'name' refers to the DB enum type name.
        # 'create_type=False' tells SQLAlchemy not to try creating the ENUM type itself,
        # as we expect it to be created by Alembic or a previous migration based on the Note model.
        nullable=True, # SQL allows NULL here
        index=True
    )

    # ai_reasoning TEXT
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # user_chosen_type memory_type_enum NOT NULL
    # + CREATE INDEX idx_aicf_user_chosen_type ON ai_categorization_feedback(user_chosen_type);
    user_chosen_type: Mapped[MemoryTypeEnum] = mapped_column(
        Enum(MemoryTypeEnum, name="memory_type_enum", create_type=False),
        nullable=False, # NOT NULL
        index=True
    )

    # was_suggestion_correct BOOLEAN
    # + CREATE INDEX idx_aicf_was_suggestion_correct ON ai_categorization_feedback(was_suggestion_correct);
    was_suggestion_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, index=True)

    # feedback_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    feedback_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), # TIMESTAMPTZ maps to DateTime(timezone=True)
        nullable=False,
        server_default=func.now() # DEFAULT CURRENT_TIMESTAMP maps to server_default=func.now()
    )

    # user_comment TEXT
    user_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<AICategorizationFeedback(id={self.id}, note_id={self.note_id}, user_chosen_type='{self.user_chosen_type.value}')>"