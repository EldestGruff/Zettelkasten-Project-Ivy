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
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from contextlib import asynccontextmanager # For lifespan events (preferred over @on_event)

# Keep original 'app.' imports - Python should now find 'backend' in sys.path
# and then look for 'app' within it.
from app.core.config import settings
from app.api.deps import get_db, DbSession
from app.api.routers import tags, notes, search, ai_tools
from app.db.vector_store import ensure_collection_exists # Import the function
from app.services.embedding import get_embedding 

# --- Lifespan Context Manager ---
# This is the modern way to handle startup/shutdown events in FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Application startup...")
    print("Ensuring Qdrant collection exists...")
    try:
        ensure_collection_exists()
        print("Qdrant collection check complete.")
    except Exception as e:
        print(f"Qdrant initialization failed: {e}")
        # Decide if the app should fail to start if Qdrant fails
        # raise e
    yield
    # Code to run on shutdown (if needed)
    print("Application shutdown...")


app = FastAPI(
    title=settings.PROJECT_NAME if hasattr(settings, 'PROJECT_NAME') else "Ivy's Second Brain API",
    version="0.1.0",
    lifespan=lifespan # Register the lifespan context manager
)


# This makes all routes defined in tags.router available under the /tags prefix
app.include_router(tags.router)
app.include_router(notes.router)
app.include_router(search.router)
app.include_router(ai_tools.router)

# --- Mount Static Files Directory ---
# This line tells FastAPI to serve files from the 'frontend/static' directory
# under the URL path '/static'.
# The 'name="static"' argument allows generating URLs for static files later if needed.
# Place this *after* API routers usually, but before the root path if serving index.html
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


# --- Root Endpoint (Can optionally serve index.html later) ---
@app.get("/")
@app.get("/")
async def serve_index():
    """ Serves the main index.html file """
    return FileResponse("frontend/index.html")

@app.get("/ping")
async def ping():
    """
    Simple health check endpoint.
    """
    return {"status": "ok", "message": "pong"}

@app.post("/test-embedding/")
async def test_embedding_endpoint(text: str):
    """ Simple endpoint to test embedding generation. """
    if not text:
        raise HTTPException(status_code=400, detail="Text query parameter is required.")
    embedding = await get_embedding(text)
    if embedding:
        return {
            "text": text,
            "embedding_preview": embedding[:5] + ["..."], # Show first 5 dimensions
            "vector_dimension": len(embedding)
            }
    else:
         raise HTTPException(status_code=500, detail="Failed to get embedding from Ollama.")

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
