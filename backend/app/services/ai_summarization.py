# backend/app/services/ai_summarization.py
import httpx
import json
from typing import Optional

from app.core.config import settings

# We can reuse the client logic or create a specific one.
# For simplicity, let's create one here, similar to the categorization client.
# In a larger app, you might centralize HTTP client creation.
_summarization_ollama_client = httpx.AsyncClient(
    base_url=settings.OLLAMA_API_BASE_URL,
    timeout=90.0, # Summarization can take a bit
    follow_redirects=True
)

async def generate_note_summary(text_content: str, max_length_chars: int = 300) -> Optional[str]:
    """
    Generates a concise summary for the given text content using an LLM.

    Args:
        text_content: The content of the note to summarize.
        max_length_chars: Approximate maximum character length for the summary.

    Returns:
        A string containing the summary, or None if summarization fails.
    """
    if not text_content or not text_content.strip():
        print("Warning: Attempted to summarize empty text.")
        return None

    # Use the categorization model for summarization for now, or define a specific one
    model_name = settings.CATEGORIZATION_MODEL_NAME # Or settings.SUMMARIZATION_MODEL_NAME
    if not model_name:
        print("Error: No summarization model configured.")
        return None

    # Truncate input text if very long to avoid excessive token usage for summarization
    # This limit should be generous enough to capture the essence.
    max_input_chars = 4000 # Example: roughly 1000 tokens
    truncated_content = text_content[:max_input_chars]
    if len(text_content) > max_input_chars:
        print(f"Warning: Input content for summarization truncated to {max_input_chars} characters.")


    # Prompt for summarization
    # Tailor the prompt for conciseness and relevance to a Zettelkasten note
    prompt = f"""
    Concisely summarize the following note content in 1 to 3 sentences.
    Focus on the main idea, key concepts, or the core question/answer presented.
    The summary should be suitable for quickly understanding the note's essence.
    The summary should ideally be less than {max_length_chars // 5} words (approx. {max_length_chars} chars).

    Note Content:
    ---
    {truncated_content}
    ---
    Concise Summary:
    """

    # Using /api/chat for instruct models is often better
    request_body = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": f"You are an AI assistant that creates concise summaries of notes. The summary should be approximately 1-3 sentences long and capture the core essence of the note. Aim for a summary length under {max_length_chars} characters."
            },
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        # "format": "json", # Not requesting JSON here, just plain text summary
        "options": { # Optional: control generation parameters
            "temperature": 0.5, # Lower temperature for more factual summaries
            # "num_predict": max_length_chars // 3 # Rough guide for token limit, model dependent
        }
    }
    endpoint_url = "/api/chat"

    print(f"Requesting summary for content (first 100 chars: '{truncated_content[:100]}...') using model: {model_name}")

    try:
        response = await _summarization_ollama_client.post(endpoint_url, json=request_body)
        response.raise_for_status()
        response_data_raw = response.json()

        summary_text = None
        if endpoint_url == "/api/chat" and response_data_raw.get("message"):
            summary_text = response_data_raw["message"]["content"].strip()
        # Add elif for /api/generate if you use that
        # elif endpoint_url == "/api/generate" and response_data_raw.get("response"):
        #    summary_text = response_data_raw["response"].strip()
        else:
            print(f"Error: Unexpected response structure from Ollama for summarization. Data: {response_data_raw}")
            return None

        if summary_text:
            print(f"LLM generated summary: '{summary_text}'")
            # Optional: Post-process summary (e.g., ensure it ends with a period, trim if too long)
            if len(summary_text) > max_length_chars * 1.2: # Allow some leeway
                summary_text = summary_text[:max_length_chars].rsplit(' ', 1)[0] + "..."
            return summary_text
        else:
            print(f"Error: LLM returned an empty summary.")
            return None

    except httpx.HTTPStatusError as e:
        print(f"HTTP error calling Ollama {endpoint_url} for summarization: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        print(f"Request error calling Ollama {endpoint_url} for summarization: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error generating summary: {e}")
        return None

# Optional: Add to FastAPI lifespan for client shutdown if needed
# async def close_summarization_client():
#     await _summarization_ollama_client.aclose()