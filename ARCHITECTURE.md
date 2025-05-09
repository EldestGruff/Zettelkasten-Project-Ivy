# Ivy Zettelkasten Project - System Architecture (Current State: Containerized + Search)

This document outlines the current architecture of the Ivy Zettelkasten project as of the implementation of semantic search and containerization of the backend.

## Architecture Diagram (Mermaid)

```mermaid
graph TD
    %% Define Styles
    classDef docker fill:#f9f,stroke:#333,stroke-width:2px;
    classDef host fill:#ccf,stroke:#333,stroke-width:2px;
    classDef external fill:#eee,stroke:#666,stroke-width:1px;
    classDef dev fill:#cfc,stroke:#333,stroke-width:1px;
    classDef storage fill:#fec,stroke:#333,stroke-width:1px;

    %% Actors / Dev Machines
    subgraph Toottoot [Dev Laptop macOS]
        USER[User]
        BROWSER["Browser / curl"]
        EDITOR["Editor / IDE"]
        GIT_CLIENT[Git Client]
    end
    class Toottoot dev

    %% Main Host Machine
    subgraph Ivy [Host Ivy Ubuntu]
        subgraph DockerNet [Docker Network: zettelkasten_net]
            direction TB
            subgraph BackendContainer [Backend Container]
                 direction TB
                 BACKEND_UVICORN["FastAPI/Uvicorn\n(main:app)"]:::docker
                 BACKEND_CODE["App Code\n(Copied via Dockerfile)"]:::docker
            end
            subgraph OllamaContainer [Ollama Container]
                 OLLAMA_SVC[Ollama Service]:::docker --> GPU[NVIDIA GPU A4500]
                 OLLAMA_SVC -- Models --- VOL_OLLAMA[(ollama_data Volume)]
            end
            subgraph QdrantContainer [Qdrant Container]
                 QDRANT_SVC[Qdrant Service]:::docker -- Data --- VOL_QDRANT[(qdrant_data Volume)]
            end
             subgraph PostgresContainer [PostgreSQL Container]
                 POSTGRES_SVC[PostgreSQL Service]:::docker -- Data --- VOL_PG[(postgres_data Volume)]
             end
        end
        class DockerNet host
    end
    class Ivy host

    %% External / Remote Services
    GITHUB[GitHub Repository]:::external

    %% Storage / Backup Target
    subgraph Moria [Host Moria TrueNAS]
         subgraph MoriaServices [Services on Moria]
             PLEX[Plex Media Server]
             NFS_SMB["(NFS/SMB Share - Planned)"]
         end
         class MoriaServices storage
    end
    class Moria storage

    %% Connections
    BROWSER -- "HTTP API (ivy:8000)" --> BACKEND_UVICORN
        %% Port exposed by Docker Compose
    %% Internal Docker Network Connections (Using Service Names)
    BACKEND_UVICORN -- "DB Connection (postgres:5432)" --> POSTGRES_SVC
    BACKEND_UVICORN -- "Vector DB Connection (qdrant:6333)" --> QDRANT_SVC
    BACKEND_UVICORN -- "Ollama Embeddings API (ollama:11434)" --> OLLAMA_SVC

    %% Development & Git
    EDITOR -- "SSH / File Sync" --> Ivy
    GIT_CLIENT -- "Git Push/Pull" --> GITHUB
    Ivy -- "Git Clone/Fetch" --> GITHUB

    %% Backup Flow
    Ivy -- "Backup Script (Planned)" --> NFS_SMB

    %% Styling Nodes
    class USER,BROWSER,EDITOR,GIT_CLIENT dev
    class GITHUB external
    class PLEX,NFS_SMB storage
    class VOL_PG,VOL_QDRANT,VOL_OLLAMA,GPU host

## Key Components & Details

1.  **Ivy (Host):**
    *   Primary application/AI host running Ubuntu.
    *   Runs the **Docker Engine** and **Docker Compose**.
    *   Hosts the entire application stack within Docker containers connected via the `zettelkasten_net` network.

2.  **Docker Containers on Ivy:**
    *   **`zettelkasten-backend`:**
        *   Runs the **FastAPI/Uvicorn** application.
        *   Built using the `backend/Dockerfile`. Code is copied into the image.
        *   Connects to other services using their *service names* (e.g., `postgres`, `qdrant`, `ollama`).
        *   Exposes port 8000 for external access (via `ivy:8000`).
        *   Handles API requests, interacts with DB/Vector Store, calls Ollama for embeddings.
    *   **`zettelkasten-postgres`:**
        *   Runs **PostgreSQL** database.
        *   Data persists via Docker volume (`postgres_data`).
        *   Accessible internally via service name `postgres` on port 5432.
    *   **`zettelkasten-qdrant`:**
        *   Runs **Qdrant** vector database.
        *   Data persists via Docker volume (`qdrant_data`).
        *   Accessible internally via service name `qdrant` on port 6333.
        *   Stores note embeddings and metadata (`is_archived`, `memory_type`).
    *   **`zettelkasten-ollama`:**
        *   Runs **Ollama** service.
        *   Models persist via Docker volume (`ollama_data`).
        *   Configured with **GPU passthrough** for acceleration.
        *   Accessible internally via service name `ollama` on port 11434.
        *   Used by the backend to generate text embeddings.

3.  **Toottoot (Dev Machine):**
    *   Development environment (macOS).
    *   Interacts with the API running on Ivy via `http://ivy:8000`.
    *   Manages Git repository.
    *   Edits code on Ivy via VS Code Remote SSH.

4.  **GitHub:**
    *   Remote Git repository.

5.  **Moria (Storage/Backup Target):**
    *   Runs TrueNAS.
    *   *Planned* target for backups of Docker volumes from Ivy.

## Data Flow (Example: Semantic Search)

1.  User enters query in UI on Toottoot.
2.  Browser sends `POST /search/similar` request with query text to `http://ivy:8000`.
3.  Docker forwards request to port 8000 of the `zettelkasten-backend` container.
4.  FastAPI routes to `search_similar_notes` endpoint.
5.  Backend calls `perform_semantic_search` service.
6.  Service calls Ollama (`http://ollama:11434/api/embeddings`) to get query vector.
7.  Service calls Qdrant (`qdrant:6333`) with query vector and filter (`is_archived=false`) using `qdrant_client.search`.
8.  Qdrant returns ranked list of matching Note UUIDs and scores.
9.  Service calls PostgreSQL (`postgres:5432`) using SQLAlchemy session to retrieve full `Note` details for the found UUIDs.
10. Service returns combined Note+Score data to the endpoint.
11. Endpoint formats data using Pydantic schemas (`SearchResponse`, `SearchResultItem`).
12. FastAPI sends JSON response back to the browser.
13. JavaScript (`app.js`) receives response and updates the search results UI.

## Implemented API Endpoints

*   `/` (Root - Serves UI)
*   `/ping` (Health check)
*   `/db-check/` (DB Connection Test)
*   `/static/*` (Serves static UI assets)
*   `/tags/` (`POST`, `GET`)
*   `/tags/{tag_id}` (`GET`, `DELETE`)
*   `/notes/` (`POST`, `GET`)
*   `/notes/{note_id}` (`GET`, `PATCH`)
*   `/notes/{note_id}/archive` (`POST`)
*   `/notes/{note_id}/unarchive` (`POST`)
*   `/notes/{note_id}/permanent` (`DELETE`)
*   `/notes/{note_id}/tags` (`GET`)
*   `/notes/{note_id}/tags/{tag_id}` (`POST`, `DELETE`)
*   `/notes/{note_id}/links/outgoing` (`GET`)
*   `/notes/{note_id}/links/incoming` (`GET`)
*   `/notes/{source_note_id}/links/{target_note_id}` (`POST`, `DELETE`)
*   `/search/similar` (`POST`)
*   `/test-embedding/` (`POST` - *Can be removed*)

## Next Steps Order (Plan)

1.  **Backend Refinements & AI Features:** (Current Focus)
    *   Error handling, logging.
    *   SQLAlchemy optimizations.
    *   API endpoint for searching tags by name.
    *   AI-driven memory type categorization.
    *   Natural Language command processing (NLU).
    *   Backup strategy implementation.
2.  **UI Enhancements:** (Can be done in parallel or after backend refinements)
    *   Styling, tag management UI, link creation UI improvements, loading indicators, etc.
3.  **STT/TTS Integration:** Add voice interaction.
4.  **Native App Development:** Plan/build Swift frontends.
5.  **Testing:** Implement unit/integration tests.
