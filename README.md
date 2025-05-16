# Ivy - Zettelkasten Second Brain Backend & UI

This project is the backend API and basic web UI for a personal knowledge management system, inspired by Zettelkasten principles and designed to act as a "second brain" companion named Ivy.

The entire application stack (FastAPI Backend, PostgreSQL, Qdrant, Ollama) is containerized using Docker and managed by Docker Compose, intended for deployment on a Linux host with NVIDIA GPU support (e.g., "Ivy"). It features a RESTful API for managing notes, tags, and links, and uses Ollama for AI-powered features like semantic search, content summarization, and memory type categorization suggestions. A simple vanilla JavaScript frontend allows for basic interaction.

## Current Status

*   **Fully Containerized Stack:** Backend, PostgreSQL, Qdrant, and Ollama (with GPU acceleration) all run as Docker containers managed by Docker Compose.
*   **Functional API:** Endpoints for full CRUD on Notes (incl. archive/delete, AI suggestions, summaries), Tags (incl. search by name), Note-Tag links, Note-Note links.
*   **Semantic Search:** API endpoint (`/search/similar`) implemented using embeddings from Ollama and vector search in Qdrant (filters archived notes).
*   **AI Features Implemented:**
    *   Embedding generation via Ollama for notes (stored in Qdrant).
    *   AI-suggested memory type for new notes (via Ollama, suggestion stored in DB).
    *   AI-generated summaries for notes (via Ollama, summary stored in DB).
    *   Feedback logging for AI categorization.
*   **Basic Web UI:** Vanilla HTML/CSS/JS served by FastAPI. Allows most API interactions, including displaying AI suggestions and summaries, and performing semantic search.
*   **Database:** PostgreSQL (v16) for structured data, schema managed via Alembic.
*   **Vector Store:** Qdrant stores embeddings and metadata.

## Technology Stack

*   **Backend:** Python 3.10+, FastAPI, Uvicorn
*   **Database ORM & Migrations:** SQLAlchemy, Alembic
*   **Database Driver:** Psycopg (for PostgreSQL)
*   **Data Validation & Settings:** Pydantic, Pydantic-Settings
*   **Database:** PostgreSQL (v16) via Docker
*   **Vector Database:** Qdrant via Docker
*   **AI / Embeddings / LLM Tasks:**
    *   Ollama via Docker (with GPU passthrough)
    *   Embedding Model (e.g., `nomic-embed-text`, configurable)
    *   Categorization/Summarization LLM (e.g., `mistral:7b-instruct-q4_K_M`, configurable)
    *   `qdrant-client`
    *   `httpx`
*   **Frontend:** Vanilla HTML, CSS, JavaScript
*   **Containerization:** Docker, Docker Compose
*   **Primary Host (Dev/Deployment):** "Ivy" - Ubuntu machine with NVIDIA GPU (A4500)
*   **Backup Target (Planned):** "Moria" - TrueNAS SCALE server

## Project Structure

See `ARCHITECTURE.md` for a detailed structure and diagram.

## Setup & Running (Fully Dockerized on Linux Host like Ivy)

**Prerequisites:**

*   Git
*   Docker & Docker Compose
*   NVIDIA GPU Drivers & NVIDIA Container Toolkit (Required on the Docker host for GPU acceleration in Ollama)

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd zettelkasten-project
    ```

2.  **Configure Environment Variables (`.env` file in project root):**
    ```dotenv
    # --- REQUIRED ---
    POSTGRES_PASSWORD=YourSecurePasswordHere! # *** REPLACE WITH YOUR STRONG PASSWORD ***

    # --- Optional Overrides / Defaults for app.core.config.Settings & Docker Compose ---
    # These are picked up by docker-compose.yml and passed to containers.
    POSTGRES_USER=zettelkasten_user
    POSTGRES_DB=zettelkasten_db
    # POSTGRES_PORT=5432 # Not needed for inter-container, only if mapping host port

    # QDRANT_PORT=6333   # Not needed for inter-container

    # OLLAMA_API_BASE_URL is http://ollama:11434 (set in docker-compose.yml for backend container)

    EMBEDDING_MODEL_NAME=nomic-embed-text
    CATEGORIZATION_MODEL_NAME=mistral:7b-instruct-q4_K_M # Or your chosen model
    QDRANT_COLLECTION_NAME=notes_embeddings

    TZ=Etc/UTC # Example: America/New_York
    ```
    *   The `POSTGRES_PASSWORD` is the most critical.
    *   Other variables like `EMBEDDING_MODEL_NAME` will be picked up by the backend container via `env_file` and the `environment` section in `docker-compose.yml`.

3.  **Build and Start Docker Services:**
    ```bash
    docker compose up --build -d
    ```
    *   `--build`: Builds the backend image using `backend/Dockerfile` and pulls/updates other service images.
    *   `-d`: Runs containers in detached mode.
    *   This command will start `postgres`, `qdrant`, `ollama`, and the `backend` service.
    *   Wait for services to initialize. Check logs: `docker compose logs -f`.

4.  **Pull Ollama Models (First time only, *inside the Ollama container*):**
    ```bash
    docker compose exec ollama ollama pull ${EMBEDDING_MODEL_NAME:-nomic-embed-text}
    docker compose exec ollama ollama pull ${CATEGORIZATION_MODEL_NAME:-mistral:7b-instruct-q4_K_M}
    ```
    (Or replace with the actual model names if not using defaults/env vars for these commands).

5.  **Run Database Migrations (First time or after schema changes, *inside the backend container*):**
    ```bash
    docker compose exec backend alembic upgrade head
    ```

## Accessing the Application

*   **Web UI:** Open your browser to `http://<ivy-ip-address>:8000/` (e.g., `http://localhost:8000/` if accessing from Ivy itself).
*   **API Docs:** Navigate to `http://<ivy-ip-address>:8000/docs` or `/redoc`.

## Next Steps / Roadmap

1.  **Backend Refinements & AI Features:** (Current Focus)
    *   Error handling, logging (Structured).
    *   SQLAlchemy optimizations (relationship loading).
    *   AI-driven memory type categorization (refine prompts, confidence scores).
    *   Automated Link Discovery (multi-pass: explicit, semantic, LLM).
    *   Natural Language command processing (NLU).
    *   Backup strategy implementation.
2.  **UI Enhancements:**
    *   Styling (`styles.css`), tag management UI (search/create by name), link creation UI improvements, loading indicators, etc.
3.  **STT/TTS Integration:** Add voice interaction.
4.  **Native App Development:** Plan/build Swift frontends.
5.  **Testing:** Implement unit/integration tests.
