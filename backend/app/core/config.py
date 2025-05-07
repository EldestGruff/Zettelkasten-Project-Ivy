# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, computed_field
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Define expected environment variables
    # Use Field(..., env=...) for explicit mapping if variable names differ
    POSTGRES_USER: str = "zettelkasten_user"
    POSTGRES_PASSWORD: str = "kV*[_G\+JA=3Iyiu1-(Lz9g);&d6]tHqqf[j3sEwV.kF4E>iAar||$[Sw}1#2xtn"
    POSTGRES_SERVER: str = "postgres" # Service name in Docker
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "zettelkasten_db"

    # Optional: Qdrant connection details
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None # If using Qdrant cloud or auth
    QDRANT_COLLECTION_NAME: str = "notes_embeddings"

    # Optional: Ollama API details
    OLLAMA_API_BASE_URL: str = "http://localhost:11434" # Default, might need adjustment
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"

    # Define the database connection URL using a computed field
    # This builds the URL from the individual components
    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """
        Construct the SQLAlchemy database URL.
        Note: PostgresDsn validates the URL format.
        """
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Load settings from a .env file if present
    # We assume the .env file is in the project root relative to where the app runs
    # Adjust env_file path if needed, e.g., based on Docker working directory
    model_config = SettingsConfigDict(env_file="../.env", extra='ignore') # Go up one level to find .env

# Create a single instance of the settings to be imported by other modules
settings = Settings()
