# Ivy Zettelkasten Project - System Architecture (Current State: Post Note/Tag CRUD)

This document outlines the current architecture of the Ivy Zettelkasten project as of the completion of the basic Note and Tag CRUD API endpoints.

## System Diagram

```ascii
+-------------------------------------------------+      +---------------------------------+      +----------------------+
| Toottoot (macOS - Dev Laptop)                   |      | Ivy (Ubuntu - AI/App Host)      |      | GitHub (Remote)      |
|-------------------------------------------------|      |---------------------------------|      |----------------------|
| +------------------+                            |      | +----------------------------+  |      | +------------------+ |
| | Browser / curl   | <--- HTTP API Calls ------> | ---> | | FastAPI/Uvicorn Process  |  | <==> | | Zettelkasten Repo| |
| | (API Client)     | (http://ivy:8000)         |      | | (Running directly in .venv)|  |      | +------------------+ |
| +------------------+                            |      | |----------------------------|  |      +----------------------+
|                                                 |      | | - main.py                  |  |
| +------------------+                            |      | | - app/ (core, db, api,    |  |              Λ
| | VS Code / Editor | --- SSH / File Sync -----> | <----| |   models, schemas, crud) |  |              | Git Push/Pull
| +------------------+                            |      | +----------------------------+  |              V
|                                                 |      |        |                      |      +----------------------+
| +------------------+                            |      |        | SQL (via SQLAlchemy)|      | Moria (TrueNAS)      |
| | Git Client       | <-------------------------> | <----|--------|  (Connects via     |      |----------------------|
| +------------------+                            |      |        V  127.0.0.1:5432)    |      | +------------------+ |
|                                                 |      | +============================+  | ---> | | NFS/SMB Share  | |<-\
+-------------------------------------------------+      | | Docker Engine              |  | |    | | (For Backups)  | | | Backup
                                                         | |----------------------------|  | |    | | *Planned*        | | | Script
                                                         | | [Network: zettelkasten_net]|  | |    | +------------------+ | | *Planned*
                                                         | |                            |  | |    |                  | | |
                                                         | | +------------------------+ |  | |    | +------------------+ | |
                                                         | | | zettelkasten-postgres  | |  | |    | | Plex Media Server| | V
                                                         | | | (PostgreSQL Container) | |  | |    | +------------------+ |
                                                         | | | Exposed: 127.0.0.1:5432| |  | |    +----------------------+
                                                         | | +------------------------+ |  | |
                                                         | |       | Data stored in     |  | |
                                                         | |       V Docker Volume      |  | |
                                                         | | +------------------------+ |  | |
                                                         | | | zettelkasten-qdrant    | |  | |
                                                         | | | (Qdrant Container)     | |  | |
                                                         | | | Exposed: 127.0.0.1:6333| |  | |
                                                         | | | *Running, NOT YET USED*| |  | |
                                                         | | +------------------------+ |  | |
                                                         | |       | Data stored in     |  | |
                                                         | |       V Docker Volume      |  | |
                                                         | +============================+  | |
                                                         |                                 | |
                                                         | +----------------------------+  | |
                                                         | | Ollama Service             |  | |
                                                         | | (LLM/Embedding Host)       |  | |
                                                         | | *Planned/Future Use*       |  | |
                                                         | +----------------------------+  | /
                                                         +---------------------------------+```

## Key Components & Details

1.  **Ivy (Host):**
    *   The primary application and AI host running Ubuntu.
    *   Runs the **Docker Engine**.
    *   Hosts the **PostgreSQL database** inside the `zettelkasten-postgres` container. Data persists via a Docker volume (`postgres_data`) on Ivy's NVMe drive. The container's port 5432 is mapped *only* to `127.0.0.1:5432` on the host.
    *   Hosts the **Qdrant vector database** inside the `zettelkasten-qdrant` container. Data persists via a Docker volume (`qdrant_data`). Port 6333 is mapped to `127.0.0.1:6333`. **Crucially, this is running but not yet integrated into the backend logic.**
    *   Currently running the **FastAPI Backend** directly via `uvicorn` within the `.venv` environment for development/testing. This process connects to PostgreSQL via `127.0.0.1:5432`.
    *   *Planned:* Will eventually host Ollama (for embeddings/NLU) and the containerized version of the FastAPI backend.

2.  **Toottoot (Dev Machine):**
    *   Your development environment (macOS).
    *   Used to edit code (synced/accessed via SSH or other means to Ivy).
    *   Used to interact with the API running on Ivy via `curl` or a browser (accessing `http://ivy:8000`).
    *   Used to manage the Git repository and sync with GitHub.

3.  **GitHub:**
    *   Remote Git repository hosting the source code for the `zettelkasten-project`.

4.  **Moria (Storage/Backup Target):**
    *   Runs TrueNAS SCALE and existing services like Plex.
    *   *Planned:* Will serve as the target for automated backups of Ivy's Docker volumes (Postgres data, Qdrant data) via NFS or SMB shares.

## Data Flow (Current)

1.  A request comes from Toottoot (e.g., `GET http://ivy:8000/tags/`) to the Uvicorn process running on Ivy.
2.  FastAPI routes the request to the appropriate endpoint function (e.g., `read_tags_endpoint`).
3.  The endpoint function uses the `DbSession` dependency to get a SQLAlchemy session.
4.  It calls a CRUD function (e.g., `crud.tag.get_tags`).
5.  The CRUD function uses the SQLAlchemy session to query the PostgreSQL database (connecting via `127.0.0.1:5432`).
6.  The database returns data to the CRUD function.
7.  The CRUD function returns SQLAlchemy model objects to the endpoint function.
8.  The endpoint function returns the model objects.
9.  FastAPI automatically converts the SQLAlchemy objects to the Pydantic `response_model` schema (e.g., `List[TagRead]`) and sends the JSON response back to Toottoot.

## Implemented API Endpoints

*   `/` (Root)
*   `/ping` (Health check)
*   `/db-check/` (DB Connection Test)
*   `/tags/` (`POST`, `GET`)
*   `/tags/{tag_id}` (`GET`, `DELETE`)
*   `/notes/` (`POST`, `GET`)
*   `/notes/{note_id}` (`GET`, `PATCH`)
*   `/notes/{note_id}/archive` (`POST`)
*   `/notes/{note_id}/unarchive` (`POST`)
*   `/notes/{note_id}/permanent` (`DELETE`)

## Next Steps Order (Plan)

1.  **Relationship Management:** Add API endpoints/logic for linking Notes <-> Tags and Notes <-> Notes.
2.  **Basic UI:** Create a frontend interface.
3.  **Qdrant Integration:** Add vector embeddings and semantic search.
4.  **Containerize Backend:** Dockerize the FastAPI application.
