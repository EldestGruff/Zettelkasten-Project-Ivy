# backend/app/schemas/tag.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional # Added Optional for potential future use

# --- Tag Base ---
# Properties shared by all Tag schemas
class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="The name of the tag") # Increased max_length example

# --- Tag Create ---
# Properties expected when creating a new tag via the API
class TagCreate(TagBase):
    pass # Creating a tag just needs the name

# --- Tag Update ---
# Properties allowed when updating a tag
class TagUpdate(TagBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="The updated name of the tag")


# --- Tag Read ---
# Properties returned when reading a tag from the API
# This schema inherits from BaseSchema for the ORM config
# It inherits from TagBase for the 'name' field
class TagRead(TagBase):
    id: int
    # Use model_config dictionary for Pydantic v2 if inheriting directly from BaseModel
    # If inheriting from our BaseSchema, config is already included.
    model_config = ConfigDict(
        from_attributes=True # Redundant if inheriting BaseSchema, but safe
    )
