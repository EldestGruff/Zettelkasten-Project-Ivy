# backend/app/services/ai_categorization.py
import httpx
import json # For parsing LLM response
from typing import Optional, Dict

from app.core.config import settings
from app.models.enums import MemoryTypeEnum # To validate the output

# Reuse or create a new client for Ollama chat/generate
# Let's use the existing one from embedding.py for now, assuming same base URL
# If different options needed, create a new client here.
# from .embedding import _ollama_client # This would create a circular dependency
# Instead, we'll re-create a client or assume it's configured similarly.

_categorization_ollama_client = httpx.AsyncClient(
    base_url=settings.OLLAMA_API_BASE_URL,
    timeout=90.0, # Categorization might take longer than embedding
    follow_redirects=True
)

async def suggest_memory_type(text_content: str) -> Optional[Dict[str, str]]:
    """
    Suggests a memory type for the given text content using an LLM.

    Args:
        text_content: The content of the note.

    Returns:
        A dictionary like {"suggested_type": "semantic", "reasoning": "..."}
        or None if categorization fails or is inconclusive.
    """
    if not text_content or not text_content.strip():
        return None

    model_name = settings.CATEGORIZATION_MODEL_NAME
    if not model_name:
        print("Error: No categorization model configured.")
        return None

    # Define valid memory types for the LLM to choose from
    valid_types = [mt.value for mt in MemoryTypeEnum if mt != MemoryTypeEnum.uncategorized]
    valid_types_str = ", ".join(valid_types) # "semantic, episodic, procedural"

    prompt = f"""
    Analyze the following note content and determine its primary memory type.
    The possible memory types are: {valid_types_str}.
    - semantic: Facts, concepts, general knowledge, definitions.
    - episodic: Personal experiences, events, memories tied to specific times/places.
    - procedural: How-to instructions, steps, processes, skills.

    Note Content:
    ---
    {text_content[:2000]}
    ---

    Based on the content, which memory type is most appropriate?
    Provide your answer in JSON format with two keys: "suggested_type" (one of [{valid_types_str}]) and "reasoning" (a brief explanation for your choice).
    Example JSON: {{"suggested_type": "semantic", "reasoning": "The note defines a concept."}}
    """
    # Using /api/chat for instruct models is often better
    request_body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are an AI assistant that categorizes notes based on their content into predefined memory types. Respond in JSON format."},
            {"role": "user", "content": prompt}
        ],
        "format": "json", # Request JSON output directly from Ollama if model supports it
        "stream": False
    }
    # For older models or /api/generate, you might use:
    # request_body = {
    #     "model": model_name,
    #     "prompt": prompt,
    #     "format": "json",
    #     "stream": False
    # }
    # endpoint_url = "/api/generate"

    endpoint_url = "/api/chat" # Use /api/chat for instruct models

    print(f"Requesting memory type categorization for content using model: {model_name}")

    try:
        response = await _categorization_ollama_client.post(endpoint_url, json=request_body)
        response.raise_for_status()
        response_data_raw = response.json()

        # For /api/chat, the content is usually in response_data_raw['message']['content']
        # For /api/generate, it's often in response_data_raw['response']
        json_response_str = ""
        if endpoint_url == "/api/chat" and response_data_raw.get("message"):
            json_response_str = response_data_raw["message"]["content"]
        elif endpoint_url == "/api/generate" and response_data_raw.get("response"):
             json_response_str = response_data_raw["response"]
        else:
            print(f"Error: Unexpected response structure from Ollama. Data: {response_data_raw}")
            return None

        print(f"DEBUG: Raw JSON string from LLM: {json_response_str}")

        try:
            # Attempt to parse the JSON string from the LLM response
            parsed_json = json.loads(json_response_str)
            suggested_type_str = parsed_json.get("suggested_type")
            reasoning = parsed_json.get("reasoning", "No reasoning provided.")

            if suggested_type_str and suggested_type_str in valid_types:
                # Validate against our Enum
                # suggested_enum_type = MemoryTypeEnum(suggested_type_str) # This line is actually not needed if we just return dict
                print(f"LLM suggested type: {suggested_type_str}, Reasoning: {reasoning}")
                return {"suggested_type": suggested_type_str, "reasoning": reasoning}
            else:
                print(f"Error: LLM returned an invalid or missing 'suggested_type'. Received: {suggested_type_str}")
                return None
        except json.JSONDecodeError as je:
            print(f"Error: Failed to parse JSON response from LLM. Raw: {json_response_str}. Error: {je}")
            return None
        except ValueError as ve: # For invalid enum value if we were converting
            print(f"Error: LLM suggested type is not a valid MemoryTypeEnum value: {suggested_type_str}. Error: {ve}")
            return None

    except httpx.HTTPStatusError as e:
        print(f"HTTP error calling Ollama {endpoint_url}: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        print(f"Request error calling Ollama {endpoint_url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error suggesting memory type: {e}")
        return None

# Optional: Add to FastAPI lifespan for client shutdown if needed
# async def close_categorization_client():
#     await _categorization_ollama_client.aclose()