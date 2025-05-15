# backend/app/schemas/note.py
import uuid
from datetime import datetime
from typing import List, Optional, Dict

from pydantic import BaseModel, Field, ConfigDict, computed_field # Import computed_field
# from pydantic import root_validator # Pydantic v1 way, or model_validator in v2

# ... (MemoryTypeEnum import or definition) ...
from .tag import TagRead
from app.models.enums import MemoryTypeEnum

class NoteBase(BaseModel):
    content: str = Field(..., description="The main content of the note")
    memory_type: MemoryTypeEnum

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    content: Optional[str] = Field(None)
    memory_type: Optional[MemoryTypeEnum] = Field(None)
    # ai_suggested_memory_type, ai_suggestion_reasoning are not directly updatable by user here
    # summary is also not directly updatable by user, it's generated


class NoteRead(NoteBase):
    id: uuid.UUID
    is_archived: bool
    summary: Optional[str] = None # <-- ADD SUMMARY FIELD HERE
    created_at: datetime
    updated_at: datetime
    tags: List[TagRead] = []
    ai_suggested_memory_type: Optional[MemoryTypeEnum] = None
    ai_suggestion_reasoning: Optional[str] = None

    # --- Construct the ai_suggestion dict for the API response ---
    @computed_field
    @property
    def ai_suggestion(self) -> Optional[Dict[str, str]]:
        if self.ai_suggested_memory_type:
            return {
                "suggested_type": self.ai_suggested_memory_type.value, # Use .value for enum string
                "reasoning": self.ai_suggestion_reasoning or "No reasoning recorded."
            }
        return None
    # -------------------------------------------------------------

    model_config = ConfigDict(from_attributes=True)


class NoteReadMinimal(BaseModel):
    id: uuid.UUID
    memory_type: MemoryTypeEnum
    is_archived: bool
    summary: Optional[str] = None 
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

