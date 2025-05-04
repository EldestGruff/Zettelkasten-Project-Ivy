# backend/app/crud/crud_tag.py
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select # Use the newer 'select' syntax

# Import the SQLAlchemy model and Pydantic schemas
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate # We'll use TagCreate/Update here

# --- Read Operations ---

def get_tag(db: Session, tag_id: int) -> Optional[Tag]:
    """
    Get a single tag by its primary key ID.

    Args:
        db: The database session.
        tag_id: The integer ID of the tag to retrieve.

    Returns:
        The Tag SQLAlchemy model object if found, otherwise None.
    """
    return db.get(Tag, tag_id) # db.get is efficient for PK lookups

def get_tag_by_name(db: Session, name: str) -> Optional[Tag]:
    """
    Get a single tag by its unique name.

    Args:
        db: The database session.
        name: The case-sensitive name of the tag to retrieve.

    Returns:
        The Tag SQLAlchemy model object if found, otherwise None.
    """
    # Prepare the SELECT statement
    statement = select(Tag).where(Tag.name == name)
    # Execute and fetch the first result (or None)
    result = db.execute(statement).scalar_one_or_none()
    return result

def get_tags(db: Session, skip: int = 0, limit: int = 100) -> List[Tag]:
    """
    Get a list of tags, with optional pagination.

    Args:
        db: The database session.
        skip: Number of records to skip (for pagination).
        limit: Maximum number of records to return (for pagination).

    Returns:
        A list of Tag SQLAlchemy model objects.
    """
    statement = select(Tag).offset(skip).limit(limit).order_by(Tag.name) # Order by name
    result = db.execute(statement).scalars().all()
    return result

# --- Create Operation ---

def create_tag(db: Session, *, tag_in: TagCreate) -> Tag:
    """
    Create a new tag in the database.

    Args:
        db: The database session.
        tag_in: Pydantic schema containing the data for the new tag.

    Returns:
        The newly created Tag SQLAlchemy model object.
    """
    # Create a SQLAlchemy model instance from the Pydantic schema data
    # `model_dump()` converts Pydantic model to dict
    db_tag = Tag(**tag_in.model_dump())
    db.add(db_tag) # Add the new object to the session
    db.commit() # Commit the transaction to save to the database
    db.refresh(db_tag) # Refresh the object to get any db-generated values (like ID)
    return db_tag

# --- Update Operation --- (Example)

def update_tag(db: Session, *, db_tag: Tag, tag_in: TagUpdate) -> Tag:
    """
    Update an existing tag.

    Args:
        db: The database session.
        db_tag: The existing Tag SQLAlchemy model object to update.
        tag_in: Pydantic schema containing the fields to update.

    Returns:
        The updated Tag SQLAlchemy model object.
    """
    # Get the dictionary of fields to update from the input schema
    # exclude_unset=True ensures we only update fields that were actually provided
    update_data = tag_in.model_dump(exclude_unset=True)

    # Update the model object's attributes
    for field, value in update_data.items():
        setattr(db_tag, field, value)

    db.add(db_tag) # Add the updated object to the session (marks it as dirty)
    db.commit() # Commit the transaction
    db.refresh(db_tag) # Refresh to get any potential database changes
    return db_tag


# --- Delete Operation --- (Example - USE WITH CAUTION)

def remove_tag(db: Session, *, tag_id: int) -> Optional[Tag]:
    """
    Permanently remove a tag by its ID.
    NOTE: Consider if tags should ever be truly deleted or just unlinked.
          If tags are shared, deleting might affect many notes.

    Args:
        db: The database session.
        tag_id: The ID of the tag to remove.

    Returns:
        The removed Tag object, or None if it didn't exist.
    """
    db_tag = db.get(Tag, tag_id)
    if db_tag:
        db.delete(db_tag)
        db.commit()
        # Note: After deletion, the db_tag object is expired,
        # accessing attributes might raise errors or return stale data.
        # Return the object mainly for confirmation or potential logging.
        return db_tag
    return None # Tag not found
