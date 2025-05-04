# backend/app/crud/crud_note.py
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete # Import update/delete for specific operations

# Import models and schemas
from app.models.note import Note
from app.models.enums import MemoryTypeEnum # Maybe needed for filtering
from app.schemas.note import NoteCreate, NoteUpdate

# --- Read Operations ---

def get_note(db: Session, note_id: uuid.UUID) -> Optional[Note]:
    """Get a single active (non-archived) note by its UUID."""
    statement = select(Note).where(Note.id == note_id, Note.is_archived == False)
    result = db.execute(statement).scalar_one_or_none()
    return result

def get_note_including_archived(db: Session, note_id: uuid.UUID) -> Optional[Note]:
    """Get a single note by UUID, regardless of archival status."""
    # db.get is simpler for PK lookups and doesn't need explicit filtering here
    return db.get(Note, note_id)

def get_notes(
    db: Session, skip: int = 0, limit: int = 100, include_archived: bool = False
) -> List[Note]:
    """
    Get a list of notes, optionally including archived ones.
    Sorted by most recently updated.
    """
    statement = select(Note)
    if not include_archived:
        statement = statement.where(Note.is_archived == False)

    statement = statement.order_by(Note.updated_at.desc()).offset(skip).limit(limit)
    result = db.execute(statement).scalars().all()
    return result

# --- Create Operation ---

def create_note(db: Session, *, note_in: NoteCreate) -> Note:
    """Create a new note."""
    # We might add logic here later to handle initial tag assignment if needed
    db_note = Note(**note_in.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    # TODO: Add Qdrant vector creation here after commit
    return db_note

# --- Update Operation ---

def update_note(db: Session, *, db_note: Note, note_in: NoteUpdate) -> Note:
    """Update an existing note."""
    update_data = note_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_note, field, value)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    # TODO: Add Qdrant vector update here after commit
    return db_note

# --- Archive / Unarchive ---

def archive_note(db: Session, *, db_note: Note) -> Note:
    """Mark a note as archived."""
    if not db_note.is_archived:
        db_note.is_archived = True
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        # TODO: Update Qdrant vector payload (is_archived=True)
    return db_note

def unarchive_note(db: Session, *, db_note: Note) -> Note:
    """Mark a note as not archived."""
    if db_note.is_archived:
        db_note.is_archived = False
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        # TODO: Update Qdrant vector payload (is_archived=False)
    return db_note

# --- Permanent Delete Operation --- (Requires careful handling)

def remove_note_permanently(db: Session, *, note_id: uuid.UUID) -> Optional[Note]:
    """
    Permanently remove a note by its ID. USE WITH EXTREME CAUTION.
    Typically only called on already archived notes after confirmation.
    """
    db_note = db.get(Note, note_id) # Get note directly by ID
    if db_note:
        # TODO: Remove from Qdrant *before* deleting from DB
        db.delete(db_note)
        db.commit()
        # Return the object mainly for confirmation
        return db_note
    return None

# --- Future: Functions for adding/removing tags/links ---
# def add_tag_to_note(...)
# def remove_tag_from_note(...)
# def link_notes(...)
# def unlink_notes(...)
