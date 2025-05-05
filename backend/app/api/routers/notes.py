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
# backend/app/api/routers/notes.py
# ... (other imports) ...
from app.schemas import TagRead # Need TagRead for response model

# ... (router definition) ...

# ... (existing Note CRUD endpoints) ...


# --- Note-Tag Association Endpoints ---

@router.post(
    "/{note_id}/tags/{tag_id}",
    response_model=NoteRead, # Return the updated note with its tags
    tags=["Notes", "Tags"] # Add to Tags group as well? Optional.
)
async def add_tag_to_note_endpoint(
    note_id: uuid.UUID,
    tag_id: int,
    db: DbSession
):
    """
    Associate an existing tag with an existing note.
    """
    # Get the note (must be active to modify?)
    db_note = crud.note.get_note(db, note_id=note_id)
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active note with ID {note_id} not found.",
        )

    # Get the tag
    db_tag = crud.tag.get_tag(db, tag_id=tag_id)
    if db_tag is None:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found.",
        )

    # Check if already associated (optional, CRUD handles it but good for clear API response)
    if db_tag in db_note.tags:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag {tag_id} ('{db_tag.name}') is already associated with note {note_id}.",
        )

    # Call the CRUD function
    updated_note = crud.note.add_tag_to_note(db=db, db_note=db_note, db_tag=db_tag)
    # Need to ensure tags are loaded for the response model serialization
    # This might require relationship loading strategies or explicit refresh logic
    # For now, let's assume FastAPI's serialization handles it (may need optimization)
    return updated_note


@router.delete(
    "/{note_id}/tags/{tag_id}",
    response_model=NoteRead, # Return the updated note
    # Or return status code 204 No Content if preferred
    # status_code=status.HTTP_204_NO_CONTENT
)
async def remove_tag_from_note_endpoint(
    note_id: uuid.UUID,
    tag_id: int,
    db: DbSession
):
    """
    Disassociate a tag from a note.
    """
    # Get the note
    db_note = crud.note.get_note(db, note_id=note_id)
    if db_note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active note with ID {note_id} not found.",
        )

    # Get the tag
    db_tag = crud.tag.get_tag(db, tag_id=tag_id)
    if db_tag is None:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found.",
        )

    # Check if association exists before trying to remove
    if db_tag not in db_note.tags:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 400 Bad Request
            detail=f"Tag {tag_id} ('{db_tag.name}') is not associated with note {note_id}.",
        )

    # Call the CRUD function
    updated_note = crud.note.remove_tag_from_note(db=db, db_note=db_note, db_tag=db_tag)
    # if status_code == 204: return None # If using 204 response
    return updated_note

# (Optional) Endpoint to get tags for a specific note
@router.get("/{note_id}/tags", response_model=List[TagRead])
async def get_tags_for_note_endpoint(
    note_id: uuid.UUID,
    db: DbSession
):
    """
    Retrieve all tags associated with a specific note.
    """
    db_note = crud.note.get_note(db, note_id=note_id)
    if db_note is None:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active note with ID {note_id} not found.",
        )
    # Access the relationship directly. FastAPI serializes based on TagRead.
    return db_note.tags

# POST /{note_id}/links/{target_note_id}
# DELETE /{note_id}/links/{link_id}

# --- Note-to-Note Linking Endpoints ---

@router.post(
    "/{source_note_id}/links/{target_note_id}",
    # response_model=LinkRead, # If we had a LinkRead schema
    status_code=status.HTTP_201_CREATED,
    summary="Create a link from source note to target note",
    # Can return the created Link object if we have a schema, or just success/failure
    # For now, let's return No Content on success to keep it simple
    response_description="Link created successfully (No content)",
    responses={
        201: {"description": "Link created successfully."},
        404: {"description": "Source or Target Note not found."},
        400: {"description": "Cannot link a note to itself."},
        409: {"description": "Link already exists."}, # If create_link raises specific error
    }
)
async def create_note_link_endpoint(
    source_note_id: uuid.UUID,
    target_note_id: uuid.UUID,
    # body: LinkCreate = None, # Optional: If accepting link_type in body
    db: DbSession
):
    """
    Create a directed link from a source note to a target note.
    """
    # Verify both notes exist (and are active?)
    source_note = crud.note.get_note(db, note_id=source_note_id)
    if source_note is None:
         raise HTTPException(status_code=404, detail=f"Source note {source_note_id} not found.")
    target_note = crud.note.get_note(db, note_id=target_note_id)
    if target_note is None:
         raise HTTPException(status_code=404, detail=f"Target note {target_note_id} not found.")

# --- Check for existing link BEFORE calling create ---
    existing_link_stmt = select(Link).where(
        Link.source_note_id == source_note_id,
        Link.target_note_id == target_note_id
    )
    existing_link = db.execute(existing_link_stmt).scalar_one_or_none()
    if existing_link:
        # Link already exists, return 409 Conflict
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Link from {source_note_id} to {target_note_id} already exists (ID: {existing_link.id})."
        )
    # --- End Check ---

    # link_type = body.link_type if body else None # Extract type if using body
    try:
        # Call CRUD function to create the link
        link = crud.link.create_link(
            db=db,
            source_note_id=source_note_id,
            target_note_id=target_note_id,
            # link_type=link_type
        )
        # If create_link returns the existing link on duplicate, we might get 200 OK instead
        # For simplicity, let's assume it raises an error or we handle it distinctly
        # Return 201 on successful creation
        # Return the Link object if using response_model=LinkRead
        # return link
        # Returning None results in 204 No Content if status_code is 204, otherwise 200 OK with null body
        # Explicitly return status for clarity if not using response_model
        # Since status_code=201, return None is okay, but let's return something minimal
        return {"detail": "Link created", "link_id": link.id} # Example minimal response

    except ValueError as e: # Catch self-linking error from CRUD
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e: # Catch potential IntegrityError etc.
        db.rollback()
         # Check if it failed because it already exists (more robust check needed in CRUD)
        existing_link = db.execute(select(Link).where(Link.source_note_id == source_note_id, Link.target_note_id == target_note_id)).scalar_one_or_none()
        if existing_link:
             raise HTTPException(status_code=409, detail="Link already exists.")
        else:
            print(f"ERROR creating link: {e}")
            raise HTTPException(status_code=500, detail="Failed to create link: {e}")


@router.delete(
    "/{source_note_id}/links/{target_note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete the link from source note to target note"
)
async def delete_note_link_endpoint(
    source_note_id: uuid.UUID,
    target_note_id: uuid.UUID,
    db: DbSession
):
    """
    Delete the specific directed link from source note to target note.
    """
    deleted = crud.link.delete_link(
        db=db,
        source_note_id=source_note_id,
        target_note_id=target_note_id
    )
    if not deleted:
        # Idempotency: If link doesn't exist, is it an error or success?
        # Returning 404 is common if the specific resource to delete isn't found.
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link from {source_note_id} to {target_note_id} not found."
        )
    # Return No Content on successful deletion
    return None


@router.get(
    "/{note_id}/links/outgoing",
    response_model=List[NoteReadMinimal], # Return minimal info about target notes
    summary="Get notes linked FROM this note"
)
async def get_outgoing_links_endpoint(
    note_id: uuid.UUID,
    db: DbSession
):
    """
    Retrieve a list of active notes that the specified note links **to**.
    """
    # Verify the source note exists and is active
    source_note = crud.note.get_note(db, note_id=note_id)
    if source_note is None:
         raise HTTPException(status_code=404, detail=f"Source note {note_id} not found.")

    target_notes = crud.link.get_outgoing_linked_notes(db=db, source_note_id=note_id)
    return target_notes


@router.get(
    "/{note_id}/links/incoming",
    response_model=List[NoteReadMinimal], # Return minimal info about source notes
    summary="Get notes linking TO this note (backlinks)"
)
async def get_incoming_links_endpoint(
    note_id: uuid.UUID,
    db: DbSession
):
    """
    Retrieve a list of active notes that link **to** the specified note (backlinks).
    """
     # Verify the target note exists and is active
    target_note = crud.note.get_note(db, note_id=note_id)
    if target_note is None:
         raise HTTPException(status_code=404, detail=f"Target note {note_id} not found.")

    source_notes = crud.link.get_incoming_linked_notes(db=db, target_note_id=note_id)
    return source_notes
