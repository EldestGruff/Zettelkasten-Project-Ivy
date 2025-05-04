# backend/main.py
from fastapi import FastAPI, Depends # Add Depends
from sqlalchemy.orm import Session # Import Session type
from sqlalchemy import text

from app.core.config import settings # Import settings
from app.api.deps import get_db, DbSession # Import dependency and type alias

# Create an instance of the FastAPI class
app = FastAPI(
    title=settings.PROJECT_NAME if hasattr(settings, 'PROJECT_NAME') else "Ivy's Second Brain API",
    version="0.1.0" # You could also load version from settings
    # Add other FastAPI options like description, openapi_url etc. if needed
)

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
