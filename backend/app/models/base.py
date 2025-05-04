# backend/app/models/base.py
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import MetaData

# Define naming conventions for constraints (optional but good practice)
# Helps ensure consistent index and constraint names across databases
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Create metadata with the naming convention
metadata_obj = MetaData(naming_convention=convention)

class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.
    Includes configuration for metadata and naming conventions.
    """
    metadata = metadata_obj

    # Optional: Automatically generate __tablename__
    # Uncomment if you prefer table names derived from class names (e.g., Note -> 'notes')
    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return cls.__name__.lower() + "s" # Example: 'notes', 'tags'
