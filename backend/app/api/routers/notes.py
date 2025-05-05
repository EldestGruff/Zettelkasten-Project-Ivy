# backend/app/api/routers/notes.py
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
# --- Need additional imports ---
from sqlalchemy import select # Needed for link pre-check
from sqlalchemy.exc import IntegrityError # To catch DB errors

from app.api.deps import DbSession
from app.schemas import (
    NoteRead,
    NoteReadMinimal,
    NoteCreate,
    NoteUpdate,
    TagRead, # Needed for tag endpoints
)
from app import crud
# --- Need Link model for pre-check ---
from app.models.link import Link # Needed for link pre-check

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
    responses={404: {"description": "Not found"}},
)

# --- Endpoint to Create a Note ---
@router.post("/", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note_endpoint(note_in: NoteCreate, db: DbSession):
    """ Create a new note. """
    try:
        created_note = crud.note.create_note(db=db, note_in=note_in)
        return created_note
    except Exception as e:
        db.rollback()
        print(f"ERROR creating note: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# --- Endpoint to Read Notes ---
@router.get("/", response_model=List[NoteReadMinimal])
async def read_notes_endpoint(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = Query(False, description="Include archived notes")
):
    """ Retrieve a list of notes (minimal view). """
    notes = crud.note.get_notes(
        db, skip=skip, limit=limit, include_archived=include_archived
    )
    return notes

# --- Endpoint to Read a Single Note ---
@router.get("/{note_id}", response_model=NoteRead)
async def read_note_endpoint(note_id: uuid.UUID, db: DbSession):
    """ Get a specific active note by its UUID. """
    db_note = crud.note.get_note(db, note_id=note_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail=f"Active note {note_id} not found")
    return db_note

# --- Endpoint to Update a Note ---
@router.patch("/{note_id}", response_model=NoteRead)
async def update_note_endpoint(note_id: uuid.UUID, note_in: NoteUpdate, db: DbSession):
    """ Update a note's content or memory type. """
    db_note = crud.note.get_note(db, note_id=note_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail=f"Active note {note_id} not found")
    if not note_in.model_dump(exclude_unset=True):
         raise HTTPException(status_code=400, detail="No update data provided.")
    try:
        updated_note = crud.note.update_note(db=db, db_note=db_note, note_in=note_in)
        return updated_note
    except Exception as e:
        db.rollback()
        print(f"ERROR updating note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# --- Endpoint to Archive a Note ---
@router.post("/{note_id}/archive", response_model=NoteRead)
async def archive_note_endpoint(note_id: uuid.UUID, db: DbSession):
    """ Mark a note as archived. """
    db_note = crud.note.get_note(db, note_id=note_id)
    if db_note is None:
        existing_note = crud.note.get_note_including_archived(db, note_id=note_id)
        if existing_note:
             raise HTTPException(status_code=400, detail="Note is already archived.")
        else:
            raise HTTPException(status_code=404, detail=f"Note {note_id} not found.")
    try:
        archived_note = crud.note.archive_note(db=db, db_note=db_note)
        return archived_note
    except Exception as e:
        db.rollback()
        print(f"ERROR archiving note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# --- Endpoint to Unarchive a Note ---
@router.post("/{note_id}/unarchive", response_model=NoteRead)
async def unarchive_note_endpoint(note_id: uuid.UUID, db: DbSession):
    """ Mark a note as active (unarchive). """
    db_note = crud.note.get_note_including_archived(db, note_id=note_id)
    if db_note is None:
         raise HTTPException(status_code=404, detail=f"Note {note_id} not found.")
    if not db_note.is_archived:
         raise HTTPException(status_code=400, detail="Note is not archived.")
    try:
        unarchived_note = crud.note.unarchive_note(db=db, db_note=db_note)
        return unarchived_note
    except Exception as e:
        db.rollback()
        print(f"ERROR unarchiving note {note_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# --- Endpoint for Permanent Deletion ---
@router.delete("/{note_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note_permanently_endpoint(note_id: uuid.UUID, db: DbSession):
    """ Permanently delete a note by ID. """
    removed_note = crud.note.remove_note_permanently(db=db, note_id=note_id)
    if removed_note is None:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found.")
    return None

# --- Note-Tag Association Endpoints ---

@router.post("/{note_id}/tags/{tag_id}", response_model=NoteRead)
async def add_tag_to_note_endpoint(note_id: uuid.UUID, tag_id: int, db: DbSession):
    """ Associate an existing tag with an existing note. """
    db_note = crud.note.get_note(db, note_id=note_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail=f"Active note {note_id} not found.")
    db_tag = crud.tag.get_tag(db, tag_id=tag_id)
    if db_tag is None:
         raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found.")
    if db_tag in db_note.tags: # Simple check using relationship loaded state (may need optimization)
        raise HTTPException(status_code=409, detail="Tag already associated.")
    updated_note = crud.note.add_tag_to_note(db=db, db_note=db_note, db_tag=db_tag)
    return updated_note

@router.delete("/{note_id}/tags/{tag_id}", response_model=NoteRead)
async def remove_tag_from_note_endpoint(note_id: uuid.UUID, tag_id: int, db: DbSession):
    """ Disassociate a tag from a note. """
    db_note = crud.note.get_note(db, note_id=note_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail=f"Active note {note_id} not found.")
    db_tag = crud.tag.get_tag(db, tag_id=tag_id)
    if db_tag is None:
         raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found.")
    if db_tag not in db_note.tags: # Simple check
        raise HTTPException(status_code=404, detail="Tag not associated with this note.")
    updated_note = crud.note.remove_tag_from_note(db=db, db_note=db_note, db_tag=db_tag)
    return updated_note

@router.get("/{note_id}/tags", response_model=List[TagRead])
async def get_tags_for_note_endpoint(note_id: uuid.UUID, db: DbSession):
    """ Retrieve all tags associated with a specific note. """
    db_note = crud.note.get_note(db, note_id=note_id)
    if db_note is None:
         raise HTTPException(status_code=404, detail=f"Active note {note_id} not found.")
    return db_note.tags

# --- Note-to-Note Linking Endpoints ---

@router.post(
    "/{source_note_id}/links/{target_note_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Create a link from source note to target note",
    response_description="Link created successfully",
    responses={
        201: {"description": "Link created successfully."},
        404: {"description": "Source or Target Note not found."},
        400: {"description": "Cannot link a note to itself."},
        409: {"description": "Link already exists."},
    }
)
async def create_note_link_endpoint(
    source_note_id: uuid.UUID,
    target_note_id: uuid.UUID,
    db: DbSession
):
    """ Create a directed link from a source note to a target note. """
    # Verify notes exist and are active
    source_note = crud.note.get_note(db, note_id=source_note_id)
    if source_note is None:
         raise HTTPException(status_code=404, detail=f"Source note {source_note_id} not found.")
    target_note = crud.note.get_note(db, note_id=target_note_id)
    if target_note is None:
         raise HTTPException(status_code=404, detail=f"Target note {target_note_id} not found.")

    # --- FIX: Check for existing link BEFORE calling create ---
    existing_link_stmt = select(Link).where(
        Link.source_note_id == source_note_id,
        Link.target_note_id == target_note_id
    )
    existing_link = db.execute(existing_link_stmt).scalar_one_or_none()
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Link from {source_note_id} to {target_note_id} already exists."
        )
    # --- End Fix ---

    try:
        link = crud.link.create_link(
            db=db, source_note_id=source_note_id, target_note_id=target_note_id
        )
        return {"detail": "Link created successfully", "link_id": link.id} # Return minimal info
    except ValueError as e: # Catch self-linking
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e: # Catch potential DB constraint violation on insert (race condition)
         db.rollback()
         raise HTTPException(status_code=409, detail=f"DB error: Link likely created concurrently.")
    except Exception as e: # Catch other unexpected errors
        db.rollback()
        print(f"ERROR creating link: {e}")
        raise HTTPException(status_code=500, detail="Failed to create link.")

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
    """ Delete the specific directed link from source note to target note. """
    deleted = crud.link.delete_link(
        db=db, source_note_id=source_note_id, target_note_id=target_note_id
    )
    if not deleted:
         raise HTTPException(status_code=404, detail="Link not found.")
    return None

@router.get(
    "/{note_id}/links/outgoing",
    response_model=List[NoteReadMinimal],
    summary="Get notes linked FROM this note"
)
async def get_outgoing_links_endpoint(note_id: uuid.UUID, db: DbSession):
    """ Retrieve a list of active notes that the specified note links TO. """
    source_note = crud.note.get_note(db, note_id=note_id)
    if source_note is None:
         raise HTTPException(status_code=404, detail=f"Source note {note_id} not found.")
    target_notes = crud.link.get_outgoing_linked_notes(db=db, source_note_id=note_id)
    return target_notes

@router.get(
    "/{note_id}/links/incoming",
    response_model=List[NoteReadMinimal],
    summary="Get notes linking TO this note (backlinks)"
)
async def get_incoming_links_endpoint(note_id: uuid.UUID, db: DbSession):
    """ Retrieve a list of active notes that link TO the specified note (backlinks). """
    target_note = crud.note.get_note(db, note_id=note_id)
    if target_note is None:
         raise HTTPException(status_code=404, detail=f"Target note {note_id} not found.")
    source_notes = crud.link.get_incoming_linked_notes(db=db, target_note_id=note_id)
    return source_notes
