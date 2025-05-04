# backend/app/models/enums.py
import enum

# Mirror the PostgreSQL ENUM type
class MemoryTypeEnum(enum.Enum):
    semantic = "semantic"
    episodic = "episodic"
    procedural = "procedural"
    uncategorized = "uncategorized"
