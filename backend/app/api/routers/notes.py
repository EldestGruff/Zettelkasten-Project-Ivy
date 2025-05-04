# backend/app/api/routers/notes.py
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query # Added Query

from app.api.deps import DbSession
from app.schemas import ( # Import multiple schemas needed
    NoteRead,
    NoteReadMinimal,
    NoteCreate,
    NoteUpdate,
)
from app import crud # Import main crud package

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
    responses={404: {"description": "Not found"}},
)

# --- Endpoint to Create a Note ---
@router.post("/", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note_endpoint(
    note_in: NoteCreate,
    db: DbSession
):
    """
    Create a new note.
    """
    # In the future, could check for duplicate content if desired
    try:
        created_note = crud.note.create_note(db=db, note_in=note_in)
        # TODO: Potentially associate tags passed in note_in.tags here
        # Note: The NoteRead response model will likely show an empty tags list initially
        return created_note
    except Exception as e:
        db.rollback()
        print(f"ERROR creating note: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the note.",
        )

# --- Endpoint to Read Notes ---
@router.get("/", response_model=List[NoteReadMinimal]) # Use minimal schema for lists
async def read_notes_endpoint(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = Query(False, description="Include archived notes in the results")
):
    """
    Retrieve a list of notes (minimal view), optionally including archived notes.
    Sorted by last updated time (descending).
    """
    notes = crud.note.get_notes(
        db, skip=skip, limit=limit, include_archived=include_archived
    )
    return notes # FastAPI converts list of Note models to list of NoteReadMinimal

# --- Endpoint to Read a Single Note ---
@router.get("/{note_id}", response_model=NoteRead) # Use full schema for single item
async def read_note_endpoint(
    note_id: uuid.UUID, # Use UUID type for path parameter validation
    db: DbSession
):
    """
    Get a specific active note by its UUID.
    """
    db_note = crud.note.get_note(db, note_id=note_id) # Gets active note only
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active note with ID {note_id} not found",
        )
    # FastAPI converts Note model to NoteRead schema, including tags if loaded
    # Note: By default tags might not be loaded efficiently here yet. We'll optimize later.
    return db_note

# --- Endpoint to Update a Note ---
@router.patch("/{note_id}", response_model=NoteRead) # Use PATCH for partial updates
async def update_note_endpoint(
    note_id: uuid.UUID,
    note_in: NoteUpdate, # Use NoteUpdate schema for partial updates
    db: DbSession
):
    """
    Update a note's content or memory type.
    """
    db_note = crud.note.get_note(db, note_id=note_id) # Get active note
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active note with ID {note_id} not found, cannot update.",
        )
    # Check if there's actually any data to update
    if not note_in.model_dump(exclude_unset=True):
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided.",
        )
    try:
        updated_note = crud.note.update_note(db=db, db_note=db_note, note_in=note_in)
        return updated_note
    except Exception as e:
        db.rollback()
        print(f"ERROR updating note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the note.",
        )

# --- Endpoint to Archive a Note ---
@router.post("/{note_id}/archive", response_model=NoteRead)
async def archive_note_endpoint(
    note_id: uuid.UUID,
    db: DbSession
):
    """
    Mark a note as archived.
    """
    db_note = crud.note.get_note(db, note_id=note_id) # Find active note
    if db_note is None:
        # Maybe check if it exists but is *already* archived?
        existing_note = crud.note.get_note_including_archived(db, note_id=note_id)
        if existing_note:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # Or 200 OK if idempotent is desired
                detail=f"Note with ID {note_id} is already archived.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with ID {note_id} not found, cannot archive.",
            )
    try:
        archived_note = crud.note.archive_note(db=db, db_note=db_note)
        return archived_note
    except Exception as e: # Should be less likely here, but good practice
        db.rollback()
        print(f"ERROR archiving note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while archiving the note.",
        )

# --- Endpoint to Unarchive a Note ---
@router.post("/{note_id}/unarchive", response_model=NoteRead)
async def unarchive_note_endpoint(
    note_id: uuid.UUID,
    db: DbSession
):
    """
    Mark a note as active (unarchive).
    """
    db_note = crud.note.get_note_including_archived(db, note_id=note_id) # Find any note
    if db_note is None:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found, cannot unarchive.",
        )
    if not db_note.is_archived:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Or 200 OK
            detail=f"Note with ID {note_id} is not archived.",
        )
    try:
        unarchived_note = crud.note.unarchive_note(db=db, db_note=db_note)
        return unarchived_note
    except Exception as e:
        db.rollback()
        print(f"ERROR unarchiving note {note_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while unarchiving the note.",
        )

# --- Endpoint for Permanent Deletion --- (Requires extra care)
@router.delete("/{note_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note_permanently_endpoint(
    note_id: uuid.UUID,
    db: DbSession
):
    """
    Permanently delete a note by ID. Requires confirmation.
    Ideally only operates on already archived notes.
    """
    # Optional: Add check to ensure note is archived first?
    # db_note = crud.note.get_note_including_archived(db, note_id=note_id)
    # if db_note is None:
    #     raise HTTPException(status_code=404, detail="Note not found.")
    # if not db_note.is_archived:
    #      raise HTTPException(status_code=400, detail="Note must be archived before permanent deletion.")

    # Add header/query param for confirmation? e.g., require ?confirm=true
    # confirm: bool = Query(..., description="Must be true to confirm permanent deletion")

    removed_note = crud.note.remove_note_permanently(db=db, note_id=note_id)
    if removed_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found, cannot delete permanently.",
        )
    # Return No Content on successful deletion
    return None # FastAPI handles 204 correctly when None is returned


# --- Future endpoints for managing tags/links on notes ---
# POST /{note_id}/tags/{tag_id}
# DELETE /{note_id}/tags/{tag_id}
# POST /{note_id}/links/{target_note_id}
# DELETE /{note_id}/links/{link_id}
