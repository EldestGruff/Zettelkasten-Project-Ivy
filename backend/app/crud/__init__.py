# backend/app/crud/__init__.py
from .crud_tag import get_tag, get_tag_by_name, get_tags, create_tag, update_tag, remove_tag, search_tags_by_name
from .crud_ai_feedback import log_categorization_feedback
from .crud_note import ( # Add Note CRUD functions
    get_note,
    get_note_including_archived,
    get_notes,
    create_note,
    update_note,
    archive_note,
    unarchive_note,
    remove_note_permanently,
    add_tag_to_note,   
    remove_tag_from_note,
)
from .crud_link import ( # Add Link CRUD functions
    create_link,
    delete_link,
    delete_link_by_id,
    get_outgoing_linked_notes,
    get_incoming_linked_notes,
)

# Import modules for namespacing
from . import crud_tag as tag
from . import crud_note as note # Add note module
from . import crud_link as link
from . import crud_ai_feedback as ai_feedback

# Import others as needed
