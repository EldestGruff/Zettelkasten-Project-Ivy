# Ivy - Zettelkasten Second Brain Backend & UI

This project is the backend API and basic web UI for a personal knowledge management system, inspired by Zettelkasten principles and designed to act as a "second brain" companion named Ivy.

It features a containerized FastAPI backend providing a RESTful API for managing notes, tags, and links. It uses PostgreSQL for structured data, Qdrant for vector embeddings, and Ollama (with GPU acceleration) for generating embeddings to power semantic search. A simple vanilla JavaScript frontend allows for basic interaction.

## Current Status

*   **Containerized Stack:** Full application stack (Backend, PostgreSQL, Qdrant, Ollama) managed via Docker Compose.
*   **Functional API:** Endpoints for full CRUD on Notes (incl. archive/delete), Tags, Note-Tag links, Note-Note links.
*   **Semantic Search:** API endpoint (`/search/similar`) implemented using embeddings from Ollama and vector search in Qdrant (filters archived notes).
*   **Basic Web UI:** Vanilla HTML/CSS/JS interface served by FastAPI. Allows viewing, creating, editing, archiving, deleting notes; adding/removing tags (by ID); creating links (by ID); displaying links; performing semantic search.
*   **Database:** PostgreSQL (v16) for structured data, schema managed via Alembic.
*   **Vector Store:** Qdrant stores embeddings and basic metadata.
*   **Embeddings:** Generated via Ollama (`nomic-embed-text` or configurable model).

## Technology Stack

*   **Backend:** Python 3.10+, FastAPI, Uvicorn
*   **Database ORM & Migrations:** SQLAlchemy, Alembic
*   **Database Driver:** Psycopg (for PostgreSQL)
*   **Data Validation & Settings:** Pydantic, Pydantic-Settings
*   **Database:** PostgreSQL (v16) via Docker
*   **Vector Database:** Qdrant via Docker
*   **AI / Embeddings:**
    *   Ollama via Docker (for hosting models)
    *   Embedding Model (e.g., `nomic-embed-text`, configurable)
    *   `qdrant-client` (for vector DB interaction)
    *   `httpx` (for Ollama API calls)
*   **Frontend:** Vanilla HTML, CSS, JavaScript
*   **Containerization:** Docker, Docker Compose
*   **Primary Host (Dev/Deployment):** "Ivy" - Ubuntu machine with NVIDIA GPU (A4500)
*   **Backup Target (Planned):** "Moria" - TrueNAS SCALE server

## Project Structure

See `ARCHITECTURE.md` for a detailed structure and diagram.

## Setup & Running with Docker Compose (Recommended)

**Prerequisites:**

*   Git
*   Docker & Docker Compose
*   NVIDIA GPU Drivers & NVIDIA Container Toolkit (Required on the Docker host - Ivy - for GPU acceleration in Ollama)

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd zettelkasten-project
    ```

2.  **Configure Environment Variables:**
    *   Copy `.env.example` (if it exists) or create a new `.env` file:
        ```bash
        # cp .env.example .env # Or...
        vi .env
        ```
    *   Edit `.env` and set **at least** the `POSTGRES_PASSWORD`. Other variables have defaults set in `docker-compose.yml` or `app/core/config.py`, but can be overridden here if needed.
        ```dotenv
        # --- REQUIRED ---
        POSTGRES_PASSWORD=YOUR_STRONG_POSTGRES_PASSWORD # *** CHANGE ME ***

        # --- Optional Overrides / Defaults ---
        # POSTGRES_USER=zettelkasten_user
        # POSTGRES_DB=zettelkasten_db
        # QDRANT_COLLECTION_NAME=notes_embeddings
        # OLLAMA_API_BASE_URL=http://ollama:11434 # Internal Docker URL, usually no need to change
        # EMBEDDING_MODEL_NAME=nomic-embed-text # Change if using a different Ollama model
        # TZ=Etc/UTC # e.g., America/New_York
        ```
    *   **Security:** Ensure `.env` is in your `.gitignore` if the repository is public.

3.  **Build and Start Docker Services:**
    ```bash
    docker compose up --build -d
    ```
    *   `--build`: Builds the backend image using `backend/Dockerfile`.
    *   `-d`: Runs containers in detached mode.
    *   This command will start `postgres`, `qdrant`, `ollama`, and the `backend` service.
    *   Wait for services to initialize. Check logs: `docker compose logs -f`.

4.  **Pull Ollama Embedding Model (First time only):**
    *   Execute the pull command *inside* the running Ollama container:
    ```bash
    docker compose exec ollama ollama pull <EMBEDDING_MODEL_NAME>
    ```
    *   Replace `<EMBEDDING_MODEL_NAME>` with the value set in your `.env` file or the default (`nomic-embed-text`).

5.  **Run Database Migrations (First time only):**
    *   Execute the Alembic upgrade command *inside* the running backend container:
    ```bash
    docker compose exec backend alembic upgrade head
    ```

## Accessing the Application

*   **Web UI:** Open your browser to `http://<ivy-ip-address>:8000/`.
*   **API Docs:** Navigate to `http://<ivy-ip-address>:8000/docs` or `/redoc`.

## Local Development (Alternative - Running Backend Outside Docker)

If you need to run the backend directly on the host (e.g., for debugging with IDE breakpoints not attached to Docker):

1.  Ensure Docker services (`postgres`, `qdrant`, `ollama`) are running (`docker compose up -d postgres qdrant ollama`).
2.  Ensure your `.env` file has `POSTGRES_SERVER=127.0.0.1`, `QDRANT_HOST=127.0.0.1`, and `OLLAMA_API_BASE_URL=http://127.0.0.1:11434` (or the correct host-accessible ports).
3.  Navigate to the `backend` directory.
4.  Create/activate the virtual environment (`python3 -m venv .venv`, `source .venv/bin/activate`).
5.  Install requirements (`pip install -r requirements.txt`).
6.  Run migrations if needed (`alembic upgrade head`).
7.  Run Uvicorn: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`.

## Next Steps / Roadmap

1.  **Backend Refinements & AI Features:** (Current Focus)
    *   Error handling, logging.
    *   SQLAlchemy optimizations (relationship loading).
    *   API endpoint for searching tags by name.
    *   AI-driven memory type categorization.
    *   Natural Language command processing (NLU).
    *   Backup strategy implementation (Ivy -> Moria).
2.  **UI Enhancements:**
    *   Styling (`styles.css`), tag management UI, link creation UI improvements, loading indicators, etc.
3.  **STT/TTS Integration:** Add voice interaction.
4.  **Native App Development:** Plan/build Swift frontends.
5.  **Testing:** Implement unit/integration tests.