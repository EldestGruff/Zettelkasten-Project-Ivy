# backend/main.py
import sys
import os
import pathlib # Using pathlib for more robust path handling

# --- Add project root's PARENT to sys.path ---
# Get the directory containing this file (backend/)
backend_dir = pathlib.Path(__file__).resolve().parent
# Get the parent directory (zettelkasten-project/) which contains the 'backend' package
project_root_parent = backend_dir.parent
# Add the directory *containing* 'backend' to the Python path
if str(project_root_parent) not in sys.path:
    sys.path.insert(0, str(project_root_parent))
    print(f"--- Added to sys.path: {project_root_parent} ---") # Debug print
# ------------------------------------

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

# Keep original 'app.' imports - Python should now find 'backend' in sys.path
# and then look for 'app' within it.
from app.core.config import settings
from app.api.deps import get_db, DbSession
from app.api.routers import tags
from app.api.routers import notes

# Create an instance of the FastAPI class
app = FastAPI(
    title=settings.PROJECT_NAME if hasattr(settings, 'PROJECT_NAME') else "Ivy's Second Brain API",
    version="0.1.0" # You could also load version from settings
    # Add other FastAPI options like description, openapi_url etc. if needed
)

# This makes all routes defined in tags.router available under the /tags prefix
app.include_router(tags.router)
app.include_router(notes.router)

@app.get("/")
async def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to Ivy's Second Brain API!"}

@app.get("/ping")
async def ping():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "message": "pong"}

# --- Example of using the DB Session Dependency ---
@app.get("/db-check/")
# Inject the session using the dependency function directly or the type alias
# async def check_database_connection(db: Session = Depends(get_db)): # Option 1
async def check_database_connection(db: DbSession): # Option 2 (using type alias)
    """
    Endpoint to test database connectivity via dependency injection.
    """
    try:
        # Try a simple query
        result = db.execute(text("SELECT 1")).scalar_one()
        if result == 1:
            return {"status": "ok", "message": "Database connection successful!"}
        else:
            # This case should not happen with "SELECT 1"
            return {"status": "error", "message": "Unexpected result from DB."}
    except Exception as e:
        # In a real app, handle exceptions more gracefully (log them, return proper HTTP errors)
        # Raise HTTPException or return a JSON response indicating failure
        print(f"DB Check Error: {e}") # Print for now
        return {"status": "error", "message": f"Database connection failed: {e}"}

# --- Future database setup, routers, etc., will go below ---
