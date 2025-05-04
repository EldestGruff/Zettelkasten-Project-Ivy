# backend/app/schemas/note.py
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

# Assuming enums.py is in app/models/ - adjust if moved
# If enums are purely for data shapes, they could live in schemas too
try:
    from app.models.enums import MemoryTypeEnum # Import the Enum for validation
except ImportError:
    # Fallback or define Enum here if models aren't available/desired dependency
    import enum
    class MemoryTypeEnum(str, enum.Enum): # Use str mixin for easy JSON serialization
        semantic = "semantic"
        episodic = "episodic"
        procedural = "procedural"
        uncategorized = "uncategorized"


from .tag import TagRead # Import TagRead to represent nested tags

# --- Note Base ---
# Properties shared across Note schemas
class NoteBase(BaseModel):
    content: str = Field(..., description="The main content of the note")
    memory_type: MemoryTypeEnum = Field(default=MemoryTypeEnum.uncategorized, description="Categorization of the note's memory type")

# --- Note Create ---
# Properties expected when creating a note via API
class NoteCreate(NoteBase):
    # Keep it simple for now: tags/links handled separately
    pass

# --- Note Update ---
# Properties allowed when updating a note (PATCH)
class NoteUpdate(BaseModel):
    content: Optional[str] = Field(None, description="Updated content of the note")
    memory_type: Optional[MemoryTypeEnum] = Field(None, description="Updated memory type")
    # Note: is_archived is usually handled by specific archive/unarchive endpoints

# --- Note Read ---
# Properties returned when reading a single note from the API
# Inherit from BaseSchema for ORM config
class NoteRead(NoteBase):
    id: uuid.UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    tags: List[TagRead] = [] # Include related tags using the TagRead schema

    model_config = ConfigDict(
        from_attributes=True
    )

# --- Note Read Minimal ---
# Schema for list views
class NoteReadMinimal(BaseModel):
    id: uuid.UUID
    memory_type: MemoryTypeEnum
    is_archived: bool
    updated_at: datetime
    # Maybe add first N characters of content?
    # content_preview: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )
