# backend/app/api/routers/tags.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from sqlalchemy.exc import IntegrityError # Import specific DB exceptions

from app.api.deps import DbSession
from app.schemas import TagRead, TagCreate
# --- Import the CRUD functions for tags ---
# We can import specific functions or the module
from app import crud # Import the main crud package
# from app.crud.crud_tag import get_tag, get_tags, create_tag # Alternative specific imports

router = APIRouter(
    prefix="/tags",
    tags=["Tags"],
    responses={404: {"description": "Not found"}},
)

# --- Endpoint to Create a Tag ---
@router.post("/", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag_endpoint( # Renamed function slightly for clarity
    tag_in: TagCreate,
    db: DbSession
):
    """
    Create a new tag. Prevents duplicate tag names.
    """
    # Check if tag already exists by name
    existing_tag = crud.tag.get_tag_by_name(db, name=tag_in.name)
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, # 409 Conflict is appropriate for duplicates
            detail=f"Tag with name '{tag_in.name}' already exists.",
        )
    try:
        # Call the CRUD function to create the tag in the DB
        created_tag = crud.tag.create_tag(db=db, tag_in=tag_in)
        return created_tag
    except IntegrityError as e: # Catch potential race conditions at DB level
         db.rollback() # Rollback the session
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database error: Tag name '{tag_in.name}' likely already exists. {e}",
        )
    except Exception as e: # Catch unexpected errors
        db.rollback()
        # Log the error in a real application!
        print(f"ERROR creating tag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the tag.",
        )


# --- Endpoint to Read Tags ---
@router.get("/", response_model=List[TagRead])
async def read_tags_endpoint(
    db: DbSession,
    name: Optional[str] = Query(None, min_length=1, description="Search query for tag name (case-insensitive, partial match)"),
    skip: int = Query(0, ge=0), # ge=0 means greater than or equal to 0
    limit: int = Query(100, ge=1, le=200) # Add some bounds to limit
):
    """
    Retrieve a list of tags.
    If 'name' query parameter is provided, searches for tags matching the name.
    Otherwise, returns a paginated list of all tags.
    """
    if name:
        # If name query is present, use the search function
        tags = crud.tag.search_tags_by_name(db, name_query=name, limit=limit)
    else:
        # Otherwise, get all tags with pagination
        tags = crud.tag.get_tags(db, skip=skip, limit=limit)

    return tags # FastAPI converts SQLAlchemy models to TagRead schemas

# --- Endpoint to Read a Single Tag by ID ---
@router.get("/{tag_id}", response_model=TagRead)
async def read_tag_endpoint( # Renamed function slightly
    tag_id: int,
    db: DbSession
):
    """
    Get a specific tag by its ID.
    """
    # Call the CRUD function to get a single tag by ID
    db_tag = crud.tag.get_tag(db, tag_id=tag_id)
    if db_tag is None:
        # If the tag doesn't exist, raise a 404 Not Found error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found",
        )
    # FastAPI converts the Tag model to TagRead schema automatically
    return db_tag


# --- Endpoint to Delete a Tag --- (Example)
@router.delete("/{tag_id}", response_model=TagRead, status_code=status.HTTP_200_OK)
async def delete_tag_endpoint( # Renamed function slightly
    tag_id: int,
    db: DbSession
):
    """
    Delete a tag by its ID. (Use with caution!)
    """
    # Call the CRUD function to remove the tag
    removed_tag = crud.tag.remove_tag(db=db, tag_id=tag_id)
    if removed_tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found, cannot delete.",
        )
    # Return the data of the deleted tag (optional)
    # Note: accessing attributes after delete might be unsafe if not handled in CRUD
    return removed_tag # FastAPI will try to convert it to TagRead

# --- We would add an endpoint for updating tags similarly ---
# @router.patch("/{tag_id}", response_model=TagRead) ... etc
