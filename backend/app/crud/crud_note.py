# backend/app/crud/crud_note.py
import uuid
import time
import logging
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, update, delete
from qdrant_client import QdrantClient, models as qdrant_models
from app.db.vector_store import get_qdrant_client
from app.core.config import settings
from app.services.embedding import get_embedding
from app.services.ai_categorization import suggest_memory_type
from app.services.ai_summarization import generate_note_summary

# Import models and schemas
from app.models.note import Note
from app.models.tag import Tag
from app.models.enums import MemoryTypeEnum
from app.schemas.note import NoteCreate, NoteUpdate

# Set up logger
logger = logging.getLogger(__name__)

# --- Read Operations ---

def get_note(db: Session, note_id: uuid.UUID) -> Optional[Note]:
    """Get a single active (non-archived) note by its UUID, eagerly loading tags."""
    statement = (
        select(Note)
        .where(Note.id == note_id, Note.is_archived == False)
        .options(
            selectinload(Note.tags), # Eagerly load tags
            # selectinload(Note.source_links), # Optionally load full source_links
            # selectinload(Note.target_links)  # Optionally load full target_links
            # Or, if just counts are needed, we might use column_property or hybrid_property
            # on the model, but for now, loading full links is simpler if needed by detail view.
        )
    )
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
    Sorted by most recently updated. Eagerly loads tags for potential future use.
    """
    statement = select(Note)
    if not include_archived:
        statement = statement.where(Note.is_archived == False)

    statement = (
        statement.options(selectinload(Note.tags)) # Eager load tags for all notes in the list
        .order_by(Note.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
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
    """Create a new note, get AI suggestion, generate summary, and store vector embedding."""
    db_note = Note(
        content=note_in.content,
        memory_type=note_in.memory_type
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    # --- Get AI suggestion & SAVE to DB ---
    ai_suggestion_saved = False
    if db_note.content: # Only if content exists
        try:
            ai_suggestion_dict = await suggest_memory_type(db_note.content)
            if ai_suggestion_dict:
                db_note.ai_suggested_memory_type = MemoryTypeEnum[ai_suggestion_dict["suggested_type"]]
                db_note.ai_suggestion_reasoning = ai_suggestion_dict.get("reasoning")
                ai_suggestion_saved = True
                # No separate commit yet, will bundle with summary or do at end
            else:
                print(f"No AI suggestion for new note {db_note.id}.")
        except Exception as ai_e:
            print(f"ERROR during AI categorization for new note {db_note.id}: {ai_e}")

    print(f"DEBUG crud_note: Attempting to generate summary for note {db_note.id}. Content exists: {bool(db_note.content)}")

    # --- Generate and SAVE Summary ---
    summary_saved = False
    if db_note.content: # Only if content exists
        try:
            summary_text = await generate_note_summary(db_note.content)
            if summary_text:
                db_note.summary = summary_text
                summary_saved = True
                print(f"Generated summary for new note {db_note.id}: '{summary_text[:50]}...'")
            else:
                print(f"Failed to generate summary for new note {db_note.id}.")
        except Exception as sum_e:
            print(f"ERROR during summary generation for new note {db_note.id}: {sum_e}")
    # -------------------------------

    # --- Commit suggestion and summary (if any) ---
    if db_note.ai_suggested_memory_type or db_note.summary or summary_saved or ai_suggestion_saved:
        db.add(db_note) # Ensure it's in session if changes were made
        db.commit()
        db.refresh(db_note)
    # --------------------------------------------

    # --- Add Embedding and Qdrant Upsert ---
    # ... (existing Qdrant upsert logic - check if payload needs db_note.summary) ...
    # For Qdrant payload, consider if summary should be part of it
    try:
        embedding = await get_embedding(db_note.content) # Embed full content
        if embedding:
            qdrant_client = get_qdrant_client()
            payload_for_qdrant = {
                "memory_type": db_note.memory_type.value,
                "is_archived": db_note.is_archived,
                "ai_suggested_type": db_note.ai_suggested_memory_type.value if db_note.ai_suggested_memory_type else None,
                # "summary_preview": db_note.summary[:100] if db_note.summary else None # Optional: add summary snippet to Qdrant payload
            }
            qdrant_client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=[
                    qdrant_models.PointStruct(
                        id=str(db_note.id),
                        vector=embedding,
                        payload=payload_for_qdrant
                    )
                ],
                wait=True
            )
            print(f"Upserted vector for new note {db_note.id} into Qdrant.")
        # ... (rest of embedding error handling) ...
    except Exception as e:
        print(f"ERROR: Failed to upsert vector for new note {db_note.id} to Qdrant: {e}")

    return db_note

# --- Update Operation ---

async def update_note(db: Session, *, db_note: Note, note_in: NoteUpdate) -> Note:
    """Update an existing note, its summary if content changed, and its vector embedding."""
    update_data = note_in.model_dump(exclude_unset=True)
    content_changed = 'content' in update_data and update_data['content'] != db_note.content
    # Check if other direct fields or payload-relevant fields changed for Qdrant/DB update
    other_fields_changed = any(k in update_data and getattr(db_note, k) != v for k, v in update_data.items() if k != 'content')


    # Apply updates to the SQLAlchemy model attributes
    for field, value in update_data.items():
        setattr(db_note, field, value)


    # --- Generate and SAVE new Summary if content changed ---
    new_summary_generated = False
    if content_changed and db_note.content:
        print(f"DEBUG crud_note: Content changed for note {db_note.id}. Attempting summary regeneration.")
        try:
            summary_text = await generate_note_summary(db_note.content)
            if summary_text:
                db_note.summary = summary_text
                new_summary_generated = True
                print(f"Generated new summary for updated note {db_note.id}: '{summary_text[:50]}...'")
            else:
                print(f"Failed to generate new summary for updated note {db_note.id}.")
        except Exception as sum_e:
            print(f"ERROR during summary generation for updated note {db_note.id}: {sum_e}")
    # ----------------------------------------------------

    # Commit if any attribute changed (content, type, archive status, or new summary)
    if content_changed or other_fields_changed or new_summary_generated:
        db.add(db_note) # Ensure it's in the session if it was detached or attributes changed
        db.commit()
        db.refresh(db_note)

    # --- Update Embedding/Payload in Qdrant ---
    # Logic to update Qdrant if content changed (regenerate embedding) or payload fields changed
    payload_fields_for_qdrant_changed = any(k in update_data for k in ['memory_type', 'is_archived'])
    # If summary is part of Qdrant payload and it changed, that's also a payload change.
    # Let's assume for now summary is not in Qdrant payload directly.

    if content_changed or payload_fields_for_qdrant_changed:
        try:
            qdrant_client = get_qdrant_client()
            new_embedding = None
            if content_changed:
                new_embedding = await get_embedding(db_note.content)

            current_payload_for_qdrant = {
                "memory_type": db_note.memory_type.value,
                "is_archived": db_note.is_archived,
                "ai_suggested_type": db_note.ai_suggested_memory_type.value if db_note.ai_suggested_memory_type else None
            }

            if new_embedding: # If content changed and embedding was successful
                qdrant_client.upsert(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points=[qdrant_models.PointStruct(id=str(db_note.id), vector=new_embedding, payload=current_payload_for_qdrant)],
                    wait=True
                )
                print(f"Upserted vector & payload for updated note {db_note.id} into Qdrant.")
            elif payload_fields_for_qdrant_changed: # Content didn't change (or embedding failed), but other payload fields did
                qdrant_client.set_payload(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    payload=current_payload_for_qdrant, # Send the full current payload
                    points=[str(db_note.id)],
                    wait=True
                )
                print(f"Updated Qdrant payload only for note {db_note.id} (content unchanged or embedding failed).")
            elif content_changed and not new_embedding:
                print(f"Warning: Content changed but failed to generate embedding for updated note {db_note.id}. Qdrant vector not updated.")

        except Exception as e:
            print(f"ERROR: Failed to update Qdrant for note {db_note.id}: {e}")
    # ---------------------------------------
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