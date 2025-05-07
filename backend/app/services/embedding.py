# backend/app/services/embedding.py
import httpx
from typing import List, Optional

from app.core.config import settings

# --- Reusable HTTP Client (Recommended) ---
# Create a client instance that can be reused for multiple requests
# Set timeout to handle potentially long embedding generation
# Configure to follow redirects and handle HTTP errors
# Use async client as our API endpoints are async
_ollama_client = httpx.AsyncClient(
    base_url=settings.OLLAMA_API_BASE_URL,
    timeout=60.0, # Increase timeout (seconds)
    follow_redirects=True
)

async def get_embedding(text: str, model_name: Optional[str] = None) -> Optional[List[float]]:
    """
    Generates an embedding for the given text using the configured Ollama service.

    Args:
        text: The text content to embed.
        model_name: Optional override for the embedding model name. Uses config default if None.

    Returns:
        A list of floats representing the embedding vector, or None if an error occurs.
    """
    if not text or not text.strip():
        print("Warning: Attempted to get embedding for empty text.")
        return None # Cannot embed empty string

    embedding_model = model_name or settings.EMBEDDING_MODEL_NAME
    if not embedding_model:
        print("Error: No embedding model configured.")
        return None

    print(f"Requesting embedding for text using model: {embedding_model}")
    request_body = {
        "model": embedding_model,
        "prompt": text
        # Optional parameters like 'options': {'temperature': 0.0} can be added if needed
    }

    try:
        response = await _ollama_client.post("/api/embeddings", json=request_body)
        response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses

        response_data = response.json()

        if "embedding" in response_data and isinstance(response_data["embedding"], list):
            print(f"Successfully received embedding vector (dimension: {len(response_data['embedding'])})")
            return response_data["embedding"]
        else:
            print(f"Error: '/api/embeddings' response did not contain a valid 'embedding' list. Response: {response_data}")
            return None

    except httpx.HTTPStatusError as e:
        print(f"HTTP error calling Ollama /api/embeddings: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        print(f"Request error calling Ollama /api/embeddings: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error getting embedding: {e}")
        return None

# --- Optional: Function to close the client cleanly on shutdown ---
async def close_ollama_client():
    """Closes the httpx client."""
    print("Closing Ollama HTTP client...")
    await _ollama_client.aclose()
