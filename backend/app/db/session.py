# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings # Import settings instance

# Create the SQLAlchemy engine
# connect_args is optional, for specific driver options if needed
# pool_pre_ping=True checks connections before use, helpful for long-running apps
engine = create_engine(
    str(settings.DATABASE_URL), # Convert PostgresDsn to string
    pool_pre_ping=True,
    # echo=True # Uncomment for debugging SQL statements
)

# Create a configured "Session" class
# autocommit=False and autoflush=False are standard defaults for web apps
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Optional: Function to test connection ---
def check_db_connection():
    try:
        # Try to create a session to test the connection
        db = SessionLocal()
        # Try a simple query
        db.execute("SELECT 1")
        db.close()
        print("Database connection successful!")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
