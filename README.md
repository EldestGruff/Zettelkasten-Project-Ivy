# Ivy - Zettelkasten Second Brain Backend & UI

This project is the backend API and basic web UI for a personal knowledge management system, inspired by Zettelkasten principles and designed to act as a "second brain" companion named Ivy.

It features a FastAPI backend providing a RESTful API for managing notes, tags, and links, persistent storage using PostgreSQL and Qdrant, and integration with Ollama for future AI-powered features like semantic search and NLU. A simple vanilla JavaScript frontend allows for basic interaction.

## Current Status (As of Note/Tag/Link CRUD & Basic UI)

*   **Functional API:** Endpoints for full CRUD operations on Notes (including archive/unarchive/permanent delete), Tags, Note-Tag associations, and Note-Note links (including listing outgoing/incoming).
*   **Basic Web UI:** Vanilla HTML/CSS/JS interface allowing listing notes, viewing note details (including tags and links), creating notes, editing notes, archiving/unarchiving, deleting, adding/removing tags (by ID), and creating links (by ID).
*   **Database Setup:** PostgreSQL container managed by Docker Compose for structured data storage. Schema managed by Alembic migrations.
*   **Vector Store Setup:** Qdrant container managed by Docker Compose. Collection initialized on application startup. Note lifecycle events (create, update, archive, delete) are integrated to add/update/remove points in Qdrant.
*   **Embedding Service Setup:** Ollama container managed by Docker Compose with GPU passthrough. Embedding model (e.g., `nomic-embed-text`) can be pulled. Service utility created to generate embeddings via Ollama API. Embeddings are generated and stored in Qdrant during note creation/updates.
*   **Local Development:** Currently tested running the FastAPI backend directly via Uvicorn on the host machine (Ivy) while database/Ollama services run in Docker.

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

zettelkasten-project/
├── backend/
│ ├── app/ # Core application code
│ │ ├── api/ # API endpoint definitions (routers, dependencies)
│ │ ├── core/ # Configuration management
│ │ ├── crud/ # Database Create, Read, Update, Delete functions
│ │ ├── db/ # Database session, vector store client setup
│ │ ├── models/ # SQLAlchemy ORM models (database tables)
│ │ ├── schemas/ # Pydantic schemas (API data shapes)
│ │ ├── services/ # Business logic, external service interactions (e.g., embeddings)
│ │ └── init.py
│ ├── frontend/ # Static files for the web UI
│ │ ├── static/
│ │ │ ├── css/
│ │ │ │ └── styles.css
│ │ │ └── js/
│ │ │ └── app.js
│ │ └── index.html # Main HTML page
│ ├── migrations/ # Alembic migration scripts
│ │ └── versions/
│ ├── .venv/ # Python virtual environment (ignored by git)
│ ├── alembic.ini # Alembic configuration
│ └── main.py # FastAPI application entry point
├── .env # Environment variables (contains secrets! See .env.example)
├── .gitignore # Specifies intentionally untracked files
├── ARCHITECTURE.md # System architecture diagram and description
├── docker-compose.yml # Docker Compose configuration for services
└── README.md # This file

## Local Development Setup (on Host similar to Ivy)

**Prerequisites:**

*   Git
*   Python 3.10+
*   Docker & Docker Compose
*   NVIDIA GPU Drivers & NVIDIA Container Toolkit (for GPU acceleration in Ollama)
*   An editor like `vi` or VS Code

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd zettelkasten-project
    ```

2.  **Configure Environment Variables:**
    *   Copy the example environment file (create `.env.example` if needed) to `.env`:
        ```bash
        # cp .env.example .env # If you create an example file
        vi .env
        ```
    *   Edit `.env` and set the following variables:
        ```dotenv
        # PostgreSQL Credentials
        POSTGRES_USER=zettelkasten_user
        POSTGRES_PASSWORD=YOUR_STRONG_POSTGRES_PASSWORD # *** CHANGE ME ***
        POSTGRES_DB=zettelkasten_db
        # Hosts/Ports for local Uvicorn testing (connecting to Docker)
        POSTGRES_SERVER=127.0.0.1
        POSTGRES_PORT=5432
        QDRANT_HOST=127.0.0.1
        QDRANT_PORT=6333
        # Ollama Configuration (Ensure matches Ollama setup)
        OLLAMA_API_BASE_URL=http://127.0.0.1:11434 # Accessible host port
        EMBEDDING_MODEL_NAME=nomic-embed-text # Or your chosen model
        # Qdrant Collection Name
        QDRANT_COLLECTION_NAME=notes_embeddings
        # Timezone (Optional)
        TZ=Etc/UTC # e.g., America/New_York
        ```
    *   **IMPORTANT:** Make sure `.env` is added to your `.gitignore` if your repository is public.

3.  **Set up Backend Environment:**
    ```bash
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    # Install dependencies
    pip install --upgrade pip
    pip install "fastapi[all]" SQLAlchemy "psycopg[binary]" alembic qdrant-client httpx pydantic-settings
    cd .. # Return to project root
    ```

4.  **Start Docker Services:**
    ```bash
    docker compose up -d postgres qdrant ollama
    ```
    *   Wait a few moments for services to initialize. Check logs with `docker compose logs -f <service_name>`.

5.  **Pull Ollama Embedding Model:**
    ```bash
    docker compose exec ollama ollama pull nomic-embed-text # Or your EMBEDDING_MODEL_NAME
    ```

6.  **Run Database Migrations:** Apply the schema to the PostgreSQL database.
    ```bash
    cd backend
    alembic upgrade head
    cd ..
    ```

## Running the Application (Local Development)

1.  **Ensure Docker services are running:** `docker compose ps` should show `postgres`, `qdrant`, and `ollama` as "Up".
2.  **Start the FastAPI Backend:** Navigate to the `backend` directory and run Uvicorn:
    ```bash
    cd backend
    source .venv/bin/activate # If not already active
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
3.  **Access the UI:** Open your web browser and navigate to `http://<ivy-ip-address>:8000/` (e.g., `http://192.168.x.y:8000/` or `http://localhost:8000/` if running on the same machine).
4.  **Access API Docs:** Navigate to `http://<ivy-ip-address>:8000/docs` for the interactive Swagger UI or `/redoc` for alternative documentation.

## Next Steps / Roadmap

1.  **Qdrant Search Implementation:**
    *   Create API endpoint (e.g., `/search/similar`) to accept text queries.
    *   Generate embedding for the query text via Ollama.
    *   Query Qdrant using the vector to find similar note IDs (filtering out archived notes).
    *   Retrieve note details from PostgreSQL based on IDs.
    *   Add search functionality to the UI.
2.  **Containerize Backend:**
    *   Create a `Dockerfile` for the `backend` application.
    *   Add the `backend` service definition to `docker-compose.yml`.
    *   Configure environment variables within `docker-compose.yml` (e.g., `DATABASE_URL` using service names like `postgres:5432`).
    *   Ensure the full stack runs via `docker compose up`.
3.  **UI Enhancements:**
    *   Improve styling (move inline styles to `styles.css`).
    *   Add tag creation/search/selection when adding tags to notes.
    *   Add better link creation UI (e.g., search/select target note).
    *   Implement client-side confirmation before permanent delete.
    *   Add loading indicators for API calls.
4.  **NLU Integration:**
    *   Set up a larger instruction-tuned LLM via Ollama.
    *   Implement FastAPI endpoint to receive natural language commands.
    *   Use LLM function calling/tool use to parse commands and map them to API calls or CRUD operations.
    *   Implement AI-powered memory type categorization.
5.  **Refinements:**
    *   More robust error handling.
    *   Logging configuration.
    *   Code cleanup and optimization (e.g., relationship loading strategies in SQLAlchemy).
    *   Testing (unit/integration tests).
    *   Backup strategy implementation (Ivy -> Moria).