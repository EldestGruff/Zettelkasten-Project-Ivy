# backend/app/services/embedding.py
import httpx
from typing import List, Optional, Dict, Any
import uuid

from sqlalchemy.orm import Session # Need Session for DB lookup
from sqlalchemy import select, Uuid # Need select and Uuid type

from app.core.config import settings
# --- Need Qdrant client and models ---
from qdrant_client import QdrantClient, models as qdrant_models
from app.db.vector_store import get_qdrant_client, VECTOR_DIMENSION # Import client and dimension
# --- Need Note model for DB lookup ---
from app.models.note import Note


# --- Reusable HTTP Client (Recommended) ---
# Create a client instance that can be reused for multiple requests
# Set timeout to handle potentially long embedding generation
# Configure to follow redirects and handle HTTP errors
# Use async client as our API endpoints are async
_ollama_client = httpx.AsyncClient(
    base_url=settings.OLLAMA_API_BASE_URL,
    timeout=60.0, # Increase timeout (seconds)
    follow_redirects=True
)

# --- Semantic Search Function ---
async def perform_semantic_search(
    *,
    query: str,
    db: Session, # Pass in DB session to retrieve note details
    limit: int = 10
) -> List[Dict[str, Any]]: # Return list of dicts including note and score
    """
    Performs semantic search using Qdrant and retrieves note details from DB.

    Args:
        query: The user's search query text.
        db: SQLAlchemy Session for database access.
        limit: Max number of results to return.

    Returns:
        A list of dictionaries, each containing the 'note' (Note model) and 'score'.
        Returns empty list if embedding fails or no results found.
    """
    print(f"Performing semantic search for query: '{query}'")

    # 1. Get embedding for the query text
    query_embedding = await get_embedding(query)
    if not query_embedding:
        print("Error: Failed to get embedding for search query.")
        return [] # Cannot search without query vector

    # Ensure embedding dimension matches collection setting
    if len(query_embedding) != VECTOR_DIMENSION:
         print(f"Error: Query embedding dimension ({len(query_embedding)}) does not match collection dimension ({VECTOR_DIMENSION}).")
         return []

    # 2. Search Qdrant collection
    qdrant_client = get_qdrant_client()
    try:
        search_result = qdrant_client.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            # --- Add Filter to exclude archived notes ---
            query_filter=qdrant_models.Filter(
                must_not=[ # Do not match points where is_archived is true
                    qdrant_models.FieldCondition(
                        key="is_archived",
                        match=qdrant_models.MatchValue(value=True)
                    )
                ]
                # Alternatively, use must=[FieldCondition(key="is_archived", match=MatchValue(value=False))]
            ),
            limit=limit,
            # with_payload=True, # Optionally retrieve payload data from Qdrant
            # with_vectors=False # Typically don't need the vector itself back
        )
        # search_result is a list of ScoredPoint objects
        print(f"Qdrant search returned {len(search_result)} potential matches.")
        if not search_result:
            return []

    except Exception as e:
        print(f"Error during Qdrant search: {e}")
        return []

    # 3. Extract IDs and Scores
    hit_ids_str = [hit.id for hit in search_result]
    # Convert UUID strings back to UUID objects for DB query
    hit_ids_uuid = []
    for id_str in hit_ids_str:
         try:
             hit_ids_uuid.append(uuid.UUID(id_str))
         except ValueError:
             print(f"Warning: Qdrant returned invalid UUID string: {id_str}")
             continue # Skip invalid IDs

    if not hit_ids_uuid:
         print("No valid UUIDs found in Qdrant results.")
         return []

    # Map IDs to scores for later use
    scores_map = {hit.id: hit.score for hit in search_result}

    # 4. Retrieve Note details from PostgreSQL
    # Use IN clause for efficient batch fetching
    notes_statement = select(Note).where(Note.id.in_(hit_ids_uuid))
    # Important: Preserve Qdrant's similarity order! Fetch from DB then re-order.
    db_notes_map = {note.id: note for note in db.execute(notes_statement).scalars().all()}

    # 5. Combine Notes and Scores, preserving Qdrant's order
    final_results = []
    for note_uuid in hit_ids_uuid: # Iterate in the order Qdrant returned
        note_obj = db_notes_map.get(note_uuid)
        if note_obj:
             # Check if somehow an archived note slipped through (shouldn't happen with filter)
             if not note_obj.is_archived:
                 final_results.append({
                     "note": note_obj,
                     "score": scores_map.get(str(note_uuid)) # Get score using string UUID from Qdrant
                 })
             else:
                  print(f"Warning: Archived note {note_uuid} retrieved from DB despite Qdrant filter.")
        else:
             print(f"Warning: Note ID {note_uuid} found in Qdrant but not in DB.")


    print(f"Returning {len(final_results)} matched notes.")
    return final_results

async def get_embedding(text: str, model_name: Optional[str] = None) -> Optional[List[float]]:
    """
    Generates an embedding for the given text using the configured Ollama service.

    Args:
        text: The text content to embed.
        model_name: Optional override for the embedding model name. Uses config default if None.

    Returns:
        A list of floats representing the embedding vector, or None if an error occurs.
    """
    if not text or not text.strip():
        print("Warning: Attempted to get embedding for empty text.")
        return None # Cannot embed empty string

    embedding_model = model_name or settings.EMBEDDING_MODEL_NAME
    if not embedding_model:
        print("Error: No embedding model configured.")
        return None

    print(f"Requesting embedding for text using model: {embedding_model}")
    request_body = {
        "model": embedding_model,
        "prompt": text
        # Optional parameters like 'options': {'temperature': 0.0} can be added if needed
    }

    try:
        response = await _ollama_client.post("/api/embeddings", json=request_body)
        response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses

        response_data = response.json()

        if "embedding" in response_data and isinstance(response_data["embedding"], list):
            print(f"Successfully received embedding vector (dimension: {len(response_data['embedding'])})")
            return response_data["embedding"]
        else:
            print(f"Error: '/api/embeddings' response did not contain a valid 'embedding' list. Response: {response_data}")
            return None

    except httpx.HTTPStatusError as e:
        print(f"HTTP error calling Ollama /api/embeddings: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        print(f"Request error calling Ollama /api/embeddings: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error getting embedding: {e}")
        return None

# --- Optional: Function to close the client cleanly on shutdown ---
async def close_ollama_client():
    """Closes the httpx client."""
    print("Closing Ollama HTTP client...")
    await _ollama_client.aclose()
