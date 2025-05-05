# backend/app/crud/crud_link.py
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, and_ # Import 'and_' for combined conditions

# Import models
from app.models.link import Link
from app.models.note import Note

# --- Create Link ---
def create_link(
    db: Session, *, source_note_id: uuid.UUID, target_note_id: uuid.UUID, link_type: Optional[str] = None
) -> Link:
    """
    Create a new link between two notes.
    Assumes source_note_id and target_note_id refer to existing notes.
    Handles potential unique constraint violations internally.

    Args:
        db: The database session.
        source_note_id: UUID of the source note.
        target_note_id: UUID of the target note.
        link_type: Optional string describing the link type.

    Returns:
        The newly created Link SQLAlchemy object.

    Raises:
        ValueError: If source_note_id and target_note_id are the same.
        IntegrityError: If the link already exists (caught and handled).
    """
    if source_note_id == target_note_id:
        raise ValueError("Cannot link a note to itself.") # Align with DB check constraint

    # Check if link already exists (optional but good practice before insert)
    existing_link_stmt = select(Link).where(
        Link.source_note_id == source_note_id,
        Link.target_note_id == target_note_id
    )
    existing_link = db.execute(existing_link_stmt).scalar_one_or_none()
    if existing_link:
        # Or raise a specific exception / return existing link
        # For simplicity, we might just rely on the DB unique constraint below
        # raise ValueError(f"Link from {source_note_id} to {target_note_id} already exists.")
        return existing_link # Return existing if found

    # Create the new link object
    db_link = Link(
        source_note_id=source_note_id,
        target_note_id=target_note_id,
        link_type=link_type
    )
    db.add(db_link)
    try:
        db.commit()
        db.refresh(db_link) # Get the generated link ID
        return db_link
    except Exception as e: # Catch potential IntegrityError from DB unique constraint
        db.rollback() # Important to rollback on failure
        # Re-fetch in case of race condition where link was created concurrently
        existing_link = db.execute(existing_link_stmt).scalar_one_or_none()
        if existing_link:
            return existing_link
        else:
            raise e # Re-raise original exception if it wasn't a uniqueness violation

# --- Delete Link ---
def delete_link(db: Session, *, source_note_id: uuid.UUID, target_note_id: uuid.UUID) -> bool:
    """
    Delete a specific directed link between two notes.

    Args:
        db: The database session.
        source_note_id: UUID of the source note.
        target_note_id: UUID of the target note.

    Returns:
        True if a link was deleted, False otherwise.
    """
    statement = delete(Link).where(
        Link.source_note_id == source_note_id,
        Link.target_note_id == target_note_id
    )
    result = db.execute(statement)
    db.commit() # Commit the delete transaction
    # result.rowcount gives the number of rows affected (deleted)
    return result.rowcount > 0

def delete_link_by_id(db: Session, *, link_id: int) -> bool:
    """
    Delete a link by its specific ID.

    Args:
        db: The database session.
        link_id: The integer ID of the link record.

    Returns:
        True if the link was deleted, False otherwise.
    """
    db_link = db.get(Link, link_id)
    if db_link:
        db.delete(db_link)
        db.commit()
        return True
    return False

# --- Get Links (Relationships) ---
# These functions retrieve the *related Notes*, not the Link objects themselves

def get_outgoing_linked_notes(db: Session, *, source_note_id: uuid.UUID) -> List[Note]:
    """
    Get all notes linked *from* the source note (targets).
    Only returns active (non-archived) target notes.
    """
    # Select target notes where a link exists from the source, and target is not archived
    statement = (
        select(Note)
        .join(Link, Note.id == Link.target_note_id) # Join Note (as target) to Link
        .where(
            Link.source_note_id == source_note_id,
            Note.is_archived == False # Ensure target note is active
        )
        .order_by(Note.updated_at.desc()) # Example ordering
    )
    result = db.execute(statement).scalars().all()
    return result

def get_incoming_linked_notes(db: Session, *, target_note_id: uuid.UUID) -> List[Note]:
    """
    Get all notes linking *to* the target note (sources) - i.e. backlinks.
    Only returns active (non-archived) source notes.
    """
     # Select source notes where a link exists to the target, and source is not archived
    statement = (
        select(Note)
        .join(Link, Note.id == Link.source_note_id) # Join Note (as source) to Link
        .where(
            Link.target_note_id == target_note_id,
            Note.is_archived == False # Ensure source note is active
        )
        .order_by(Note.updated_at.desc()) # Example ordering
    )
    result = db.execute(statement).scalars().all()
    return result
