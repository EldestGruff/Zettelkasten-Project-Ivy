# backend/app/schemas/ai_feedback.py
import uuid
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict # Ensure ConfigDict for Pydantic v2
from datetime import datetime # Import datetime

# Assuming MemoryTypeEnum is in app.models.enums
# If not, you might need to define a simple string enum here for schema validation
try:
    from app.models.enums import MemoryTypeEnum
except ImportError:
    import enum
    class MemoryTypeEnum(str, enum.Enum):
        semantic = "semantic"
        episodic = "episodic"
        procedural = "procedural"
        uncategorized = "uncategorized"


class AICategorizationFeedbackCreate(BaseModel):
    note_id: uuid.UUID
    note_content_snippet: Optional[str] = Field(None, max_length=1000)
    prompt_used: Optional[str] = None # Optional: store the prompt if you vary it
    ai_suggested_type: Optional[MemoryTypeEnum] = None
    ai_reasoning: Optional[str] = None
    user_chosen_type: MemoryTypeEnum # What the user finally decided
    # was_suggestion_correct is derived on backend or could be explicit from UI
    user_comment: Optional[str] = None


class AICategorizationFeedbackRead(AICategorizationFeedbackCreate):
    id: int
    feedback_timestamp: datetime
    was_suggestion_correct: Optional[bool] = None # This will be set by CRUD

    model_config = ConfigDict(from_attributes=True) # For Pydantic v2