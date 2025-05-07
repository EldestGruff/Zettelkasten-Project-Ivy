# backend/app/db/vector_store.py
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import settings

# --- Qdrant Client Initialization ---
# Create a single client instance to be reused
# Use host and port from settings
qdrant_client = QdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT
    # api_key=settings.QDRANT_API_KEY, # Uncomment if using API key
    # prefer_grpc=True, # Set to True if gRPC port (6334) is mapped and preferred
)

# --- Embedding Configuration (Get dimensions based on model) ---
# TODO: Determine vector dimensions dynamically based on EMBEDDING_MODEL_NAME
#       This might involve calling the Ollama API or having a config map.
#       For now, hardcode based on chosen model (e.g., nomic-embed-text is 768)
#       Common dimensions: all-minilm: 384, nomic-embed-text: 768, mxbai-embed-large: 1024
VECTOR_DIMENSION = 768 # HARDCODED FOR nomic-embed-text - CHANGE IF MODEL CHANGES
VECTOR_DISTANCE_METRIC = Distance.COSINE # Cosine similarity is common for text embeddings

# --- Collection Initialization Logic ---
def ensure_collection_exists():
    """
    Checks if the configured Qdrant collection exists and creates it if not.
    This should be called on application startup.
    """
    collection_name = settings.QDRANT_COLLECTION_NAME
    try:
        collection_info = qdrant_client.get_collection(collection_name=collection_name)
        print(f"Qdrant collection '{collection_name}' already exists.")
        # Optional: Check if vector params match and recreate/update if needed
        # current_params = collection_info.vectors_config.params
        # if current_params.size != VECTOR_DIMENSION or current_params.distance != VECTOR_DISTANCE_METRIC:
        #     print(f"Warning: Collection vector params mismatch. Recreating?") # Handle this case if needed
    except Exception as e:
        # Catching broad exception, check if it's a "not found" type error
        # A more robust check would inspect the specific exception type/status code
        print(f"Qdrant collection '{collection_name}' not found or error checking: {e}. Attempting to create...")
        try:
            qdrant_client.recreate_collection( # Use recreate_collection for simplicity (idempotent)
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=VECTOR_DIMENSION,
                    distance=VECTOR_DISTANCE_METRIC
                )
                # Add other config like HNSW indexing later for performance
                # hnsw_config=models.HnswConfig(...)
                # optimizers_config=models.OptimizersConfigDiff(...)
            )
            print(f"Qdrant collection '{collection_name}' created successfully.")
        except Exception as create_e:
            print(f"FATAL: Failed to create Qdrant collection '{collection_name}': {create_e}")
            # Depending on severity, might want to raise error and stop app startup
            raise create_e

# --- Helper Function (Example - We'll use specific functions later) ---
def get_qdrant_client() -> QdrantClient:
    """Returns the initialized Qdrant client instance."""
    return qdrant_client
