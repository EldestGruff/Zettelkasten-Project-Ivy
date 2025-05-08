# backend/app/api/routers/search.py
from fastapi import APIRouter, HTTPException, status, Depends, Body # Added Body

from app.api.deps import DbSession
from app.schemas import SearchQuery, SearchResponse, SearchResultItem # Import search schemas
from app.services.embedding import perform_semantic_search # Import the search function

router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={500: {"description": "Internal server error during search"}},
)

@router.post(
    "/similar", # e.g., POST /search/similar
    response_model=SearchResponse
)
async def search_similar_notes(
    search_query: SearchQuery, # Get query/limit from request body
    db: DbSession # Inject DB session
):
    """
    Perform semantic search to find notes similar to the query text.
    Returns a list of matching notes (minimal view) with similarity scores.
    Filters out archived notes.
    """
    try:
        # Call the service function to perform the search
        search_results_raw = await perform_semantic_search(
            query=search_query.query,
            db=db,
            limit=search_query.limit
        )

        # Convert the raw results (list of dicts with Note models)
        # into the structure expected by the SearchResponse schema
        results_formatted = []
        for item in search_results_raw:
            # Create SearchResultItem: combines NoteReadMinimal fields + score
            # Pydantic automatically extracts fields from the Note model via from_attributes
            results_formatted.append(
                SearchResultItem(score=item["score"], **item["note"].__dict__)
                # Alternatively, manually map fields if __dict__ isn't robust enough
                # SearchResultItem(
                #     id=item["note"].id,
                #     memory_type=item["note"].memory_type,
                #     is_archived=item["note"].is_archived,
                #     updated_at=item["note"].updated_at,
                #     score=item["score"]
                # )
            )

        return SearchResponse(query=search_query.query, results=results_formatted)

    except Exception as e:
        print(f"Error during semantic search endpoint execution: {e}")
        # Consider more specific error handling based on potential exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform semantic search: {e}"
        )