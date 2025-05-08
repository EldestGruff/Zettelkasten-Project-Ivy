# backend/app/schemas/search.py
from pydantic import BaseModel, Field
from typing import List
import uuid

from .note import NoteReadMinimal # Reuse minimal note schema for results

# Schema for the search query input
class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="The text query for semantic search.")
    limit: int = Field(default=10, gt=0, le=100, description="Maximum number of results to return.")
    # Add other potential fields like filters later if needed

# Schema for a single search result item, including score
class SearchResultItem(NoteReadMinimal): # Inherits fields from NoteReadMinimal
    score: float = Field(..., description="Similarity score returned by the vector search.")

# Schema for the overall search response
class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]