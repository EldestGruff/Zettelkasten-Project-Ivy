# backend/app/crud/crud_note.py
import uuid
import time
import logging
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from qdrant_client import QdrantClient, models as qdrant_models
from app.db.vector_store import get_qdrant_client
from app.core.config import settings
from app.services.embedding import get_embedding

# Import models and schemas
from app.models.note import Note
from app.models.tag import Tag
from app.models.enums import MemoryTypeEnum
from app.schemas.note import NoteCreate, NoteUpdate

# Set up logger
logger = logging.getLogger(__name__)

# --- Read Operations ---

def get_note(db: Session, note_id: uuid.UUID) -> Optional[Note]:
    """Get a single active (non-archived) note by its UUID."""
    statement = select(Note).where(Note.id == note_id, Note.is_archived == False)
    result = db.execute(statement).scalar_one_or_none()
    return result

def get_note_including_archived(db: Session, note_id: uuid.UUID) -> Optional[Note]:
    """Get a single note by UUID, regardless of archival status."""
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

# --- Vector/Qdrant Helper Functions ---

def _build_note_payload(db_note: Note) -> Dict[str, Any]:
    """
    Build a consistent payload for Qdrant points.
    Extracted to ensure consistency across create/update operations.
    """
    # Important: Convert enum to string value explicitly
    memory_type_value = db_note.memory_type.value if db_note.memory_type else None
    
    return {
        "memory_type": memory_type_value,
        "is_archived": db_note.is_archived,
        # Add other fields if needed for filtering later
        "note_id": str(db_note.id),  # Redundant but useful for debugging
    }

async def _upsert_vector(db_note: Note, embedding: List[float]) -> bool:
    """
    Helper to handle vector upsertion with proper error handling.
    Returns True if successful, False on failure.
    """
    if not embedding:
        logger.warning(f"No embedding provided for note {db_note.id}, skipping Qdrant upsert")
        return False
        
    try:
        # Build the payload consistently
        payload = _build_note_payload(db_note)
        logger.debug(f"Upserting vector for note {db_note.id} with payload: {payload}")
        logger.debug(f"Embedding dimensions: {len(embedding)}, first values: {embedding[:5]}...")
        
        qdrant_client = get_qdrant_client()
        qdrant_client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[
                qdrant_models.PointStruct(
                    id=str(db_note.id),
                    vector=embedding,
                    payload=payload
                )
            ],
            wait=True
        )
        logger.info(f"Successfully upserted vector for note {db_note.id} into Qdrant")
        return True
    except Exception as e:
        logger.error(f"Failed to upsert vector for note {db_note.id} to Qdrant: {e}", exc_info=True)
        return False

async def _update_vector_payload(db_note: Note) -> bool:
    """
    Helper to update only the payload in Qdrant.
    Returns True if successful, False on failure.
    """
    try:
        payload = _build_note_payload(db_note)
        logger.debug(f"Updating Qdrant payload for note {db_note.id}: {payload}")
        
        qdrant_client = get_qdrant_client()
        qdrant_client.set_payload(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            payload=payload,
            points=[str(db_note.id)],
            wait=True
        )
        logger.info(f"Successfully updated payload for note {db_note.id} in Qdrant")
        return True
    except Exception as e:
        logger.error(f"Failed to update payload for note {db_note.id} in Qdrant: {e}", exc_info=True)
        return False

async def _delete_vector(note_id: uuid.UUID) -> bool:
    """
    Helper to delete a vector from Qdrant.
    Returns True if successful, False on failure.
    """
    try:
        note_id_str = str(note_id)
        logger.debug(f"Deleting vector for note {note_id_str} from Qdrant")
        
        qdrant_client = get_qdrant_client()
        qdrant_client.delete(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points_selector=qdrant_models.PointIdsList(points=[note_id_str]),
            wait=True
        )
        logger.info(f"Successfully deleted vector for note {note_id_str} from Qdrant")
        return True
    except Exception as e:
        logger.error(f"Failed to delete vector for note {note_id_str} from Qdrant: {e}", exc_info=True)
        return False

# --- Create Operation ---

async def create_note(db: Session, *, note_in: NoteCreate) -> Note:
    """Create a new note and its vector embedding."""
    # Log the incoming request details
    logger.info(f"Creating new note with memory_type: {note_in.memory_type}")
    logger.debug(f"Note content length: {len(note_in.content) if note_in.content else 0}")
    
    # Create the note in the database
    db_note = Note(**note_in.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    logger.info(f"Created note in database with ID: {db_note.id}")
    
    # Add a small delay to ensure transaction visibility (testing for race conditions)
    time.sleep(0.1)
    
    # Generate embedding and store in vector DB
    try:
        # Special debug for semantic type notes
        if db_note.memory_type == MemoryTypeEnum.semantic:
            logger.info(f"Processing semantic note {db_note.id} - special handling")
            
        # Generate embedding
        logger.debug(f"Generating embedding for note {db_note.id}")
        embedding = await get_embedding(db_note.content)
        
        if embedding:
            logger.info(f"Generated embedding for note {db_note.id}, dimensions: {len(embedding)}")
            success = await _upsert_vector(db_note, embedding)
            if not success:
                logger.warning(f"Note {db_note.id} created in database but vector storage failed")
        else:
            logger.warning(f"Failed to generate embedding for note {db_note.id}, vector not stored")
    except Exception as e:
        # Catch any other exceptions that might occur
        logger.error(f"Error during embedding/vector operations for note {db_note.id}: {e}", exc_info=True)
    
    return db_note

# --- Update Operation ---

async def update_note(db: Session, *, db_note: Note, note_in: NoteUpdate) -> Note:
    """Update an existing note and its vector embedding if content changed."""
    update_data = note_in.model_dump(exclude_unset=True)
    
    # Check what's changing for vector store updates
    content_changed = 'content' in update_data and update_data['content'] != db_note.content
    memory_type_changed = 'memory_type' in update_data and update_data['memory_type'] != db_note.memory_type
    archive_status_changed = 'is_archived' in update_data and update_data['is_archived'] != db_note.is_archived
    payload_changed = memory_type_changed or archive_status_changed
    
    logger.info(f"Updating note {db_note.id}, content_changed: {content_changed}, payload_changed: {payload_changed}")
    
    # Apply updates to the SQLAlchemy model
    for field, value in update_data.items():
        setattr(db_note, field, value)
    
    # Commit the changes to the database
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    logger.info(f"Updated note {db_note.id} in database")
    
    # Special debug log for semantic notes
    if db_note.memory_type == MemoryTypeEnum.semantic:
        logger.info(f"Note {db_note.id} is semantic type after update")
    
    # Small delay to ensure transaction visibility
    time.sleep(0.1)
    
    # Update the vector store as needed
    if content_changed:
        # If content changed, regenerate embedding and upsert
        try:
            logger.debug(f"Regenerating embedding for updated note {db_note.id}")
            new_embedding = await get_embedding(db_note.content)
            
            if new_embedding:
                logger.info(f"Generated new embedding for note {db_note.id}, dimensions: {len(new_embedding)}")
                await _upsert_vector(db_note, new_embedding)
            else:
                logger.warning(f"Failed to generate new embedding for note {db_note.id}")
                # If payload also changed, still try to update it
                if payload_changed:
                    await _update_vector_payload(db_note)
        except Exception as e:
            logger.error(f"Error updating vector for note {db_note.id}: {e}", exc_info=True)
    
    elif payload_changed:
        # If only metadata changed, just update the payload
        try:
            await _update_vector_payload(db_note)
        except Exception as e:
            logger.error(f"Error updating vector payload for note {db_note.id}: {e}", exc_info=True)
    
    return db_note

# --- Archive / Unarchive ---

async def archive_note(db: Session, *, db_note: Note) -> Note:
    """Mark a note as archived and update its Qdrant payload."""
    if not db_note.is_archived:
        logger.info(f"Archiving note {db_note.id}")
        db_note.is_archived = True
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        
        # Update Qdrant payload
        try:
            await _update_vector_payload(db_note)
        except Exception as e:
            logger.error(f"Failed to update archive status in Qdrant for note {db_note.id}: {e}", exc_info=True)
    else:
        logger.info(f"Note {db_note.id} is already archived, no action needed")
    
    return db_note

async def unarchive_note(db: Session, *, db_note: Note) -> Note:
    """Mark a note as active (unarchive) and update its Qdrant payload."""
    if db_note.is_archived:
        logger.info(f"Unarchiving note {db_note.id}")
        db_note.is_archived = False
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        
        # Update Qdrant payload
        try:
            await _update_vector_payload(db_note)
        except Exception as e:
            logger.error(f"Failed to update archive status in Qdrant for note {db_note.id}: {e}", exc_info=True)
    else:
        logger.info(f"Note {db_note.id} is already active, no action needed")
    
    return db_note

# --- Permanent Delete Operation ---

async def remove_note_permanently(db: Session, *, note_id: uuid.UUID) -> Optional[Note]:
    """
    Permanently remove a note by ID from DB and Qdrant. USE WITH EXTREME CAUTION.
    """
    logger.info(f"Attempting to permanently remove note {note_id}")
    
    db_note = db.get(Note, note_id)
    if db_note:
        # Store info before deletion
        note_uuid_str = str(db_note.id)
        memory_type = db_note.memory_type
        
        # Delete from Qdrant first
        logger.info(f"Deleting vector for note {note_uuid_str} (type: {memory_type}) from Qdrant")
        vector_deleted = await _delete_vector(db_note.id)
        
        if not vector_deleted:
            logger.warning(f"Vector deletion failed for note {note_uuid_str}, proceeding with database deletion")
        
        # Delete from PostgreSQL
        db.delete(db_note)
        db.commit()
        logger.info(f"Successfully deleted note {note_uuid_str} from database")
        
        return db_note
    
    logger.warning(f"Note {note_id} not found, nothing to delete")
    return None

# --- Note-Tag Relationship Management ---

def add_tag_to_note(db: Session, *, db_note: Note, db_tag: Tag) -> Note:
    """Associate an existing tag with an existing note."""
    logger.info(f"Adding tag {db_tag.id} ({db_tag.name}) to note {db_note.id}")
    
    # Check if association already exists
    if db_tag not in db_note.tags:
        db_note.tags.append(db_tag)
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        logger.info(f"Successfully added tag {db_tag.id} to note {db_note.id}")
    else:
        logger.info(f"Tag {db_tag.id} already associated with note {db_note.id}, no action needed")
    
    return db_note

def remove_tag_from_note(db: Session, *, db_note: Note, db_tag: Tag) -> Note:
    """Disassociate a tag from a note."""
    logger.info(f"Removing tag {db_tag.id} ({db_tag.name}) from note {db_note.id}")
    
    # Check if association exists before trying to remove
    if db_tag in db_note.tags:
        db_note.tags.remove(db_tag)
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        logger.info(f"Successfully removed tag {db_tag.id} from note {db_note.id}")
    else:
        logger.info(f"Tag {db_tag.id} not associated with note {db_note.id}, no action needed")
    
    return db_note

# --- For Future Implementation ---
# def link_notes(...)
# def unlink_notes(...)