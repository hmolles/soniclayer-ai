import os
import json
import requests
from requests.exceptions import RequestException, Timeout

BASE_URL = os.getenv("LANGFLOW_BASE_URL", "http://localhost:7860")

def call_langflow_chain(flow_name: str, segment: dict) -> dict:
    """
    Sends a segment payload to the Langflow microservice for the specified flow.
    Returns structured feedback including score, opinion, rationale, and confidence.

    Args:
        flow_name: Name of the Langflow flow (e.g., "genz_chain", "advertiser_chain")
        segment: JSON-serializable dict with segment data

    Raises:
        TimeoutError: if Langflow does not respond in time.
        ValueError: if response is malformed or missing fields.
        RequestException: for other HTTP errors.
    """
    url = f"{BASE_URL}/api/v1/run/{flow_name}"
    max_retries = 3
    timeout_seconds = 30  # Increased for LLM processing time
    
    # Langflow API headers
    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.getenv("LANGFLOW_API_KEY", "sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs")
    }

    for attempt in range(max_retries):
        try:
            # Langflow expects this specific payload structure
            payload = {
                "input_value": segment,
                "output_type": "chat",
                "input_type": "chat"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=timeout_seconds)
            response.raise_for_status()
            result = response.json()
            
            # Extract the actual message from Langflow's nested response structure
            # Response format: {outputs: [{outputs: [{results: {message: {text: "JSON_STRING"}}}]}]}
            try:
                message_text = result["outputs"][0]["outputs"][0]["results"]["message"]["text"]
                data = json.loads(message_text)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise ValueError(f"Failed to parse Langflow response structure: {e}")

            # Validate required fields
            required_fields = ["score", "opinion", "rationale", "confidence"]
            if not all(field in data for field in required_fields):
                raise ValueError(f"Missing expected fields in Langflow response. Got: {data.keys()}")

            # Validate score and confidence
            if not (1 <= data["score"] <= 5):
                raise ValueError(f"Score out of expected range (1–5), got: {data['score']}")
            if not isinstance(data["confidence"], (float, int)):
                raise ValueError(f"Confidence must be a number, got: {type(data['confidence'])}")

            return data

        except Timeout:
            if attempt == max_retries - 1:
                raise TimeoutError("Langflow request timed out after {max_retries} attempts")
        except RequestException as e:
            if attempt == max_retries - 1:
                raise RequestException(f"Langflow request failed: {e}")
        except ValueError as ve:
            raise ve
