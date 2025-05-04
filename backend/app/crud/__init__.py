# backend/app/crud/__init__.py
from .crud_tag import get_tag, get_tag_by_name, get_tags, create_tag, update_tag, remove_tag
from .crud_note import ( # Add Note CRUD functions
    get_note,
    get_note_including_archived,
    get_notes,
    create_note,
    update_note,
    archive_note,
    unarchive_note,
    remove_note_permanently,
)

# Import modules for namespacing
from . import crud_tag as tag
from . import crud_note as note # Add note module

# Import others as needed
