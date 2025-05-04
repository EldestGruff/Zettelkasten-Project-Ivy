# backend/app/models/__init__.py
from .base import Base # Ensure Base is imported
from .enums import MemoryTypeEnum # Import Enums if needed directly
from .note import Note
from .tag import Tag
from .link import Link
from .note_tag import NoteTag # Import the association model too
