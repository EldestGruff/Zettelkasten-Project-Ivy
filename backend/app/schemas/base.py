# backend/app/schemas/base.py
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """
    Base Pydantic schema configuration.

    Configures schemas to work well with ORM models.
    """
    # Use model_config dictionary for Pydantic v2
    model_config = ConfigDict(
        from_attributes=True # Allow creating schemas from ORM model attributes
    )
