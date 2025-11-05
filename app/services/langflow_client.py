import os
import json
from openai import AzureOpenAI

# Azure GPT-4o-mini configuration for Langflow replacement
AZURE_GPT_ENDPOINT = "https://hf2025-soniclayerai.cognitiveservices.azure.com"
AZURE_GPT_KEY = os.getenv("AZURE_GPT_KEY")
AZURE_GPT_DEPLOYMENT = "gpt-4o-mini"
AZURE_GPT_API_VERSION = "2025-01-01-preview"

# Persona prompts
PERSONA_PROMPTS = {
    "genz_chain": {
        "system": "You are a Gen Z content evaluator. You love humorous, exciting, and pop-culture-related content. You dislike boring, overly formal, or outdated references.",
        "user_template": """Evaluate this audio segment from a Gen Z perspective:

Text: "{text}"
Topic: {topic}
Tone: {tone}

Rate this segment on a scale of 1-5 (5 being best) and provide:
1. score (1-5)
2. opinion (brief reaction, use Gen Z slang if appropriate)
3. rationale (why you gave this score)
4. confidence (0.0-1.0, how confident you are in this rating)

Respond ONLY with JSON:
{{"score": <number>, "opinion": "<text>", "rationale": "<text>", "confidence": <number>}}"""
    },
    "advertiser_chain": {
        "system": "You are a brand safety evaluator for advertisers. You favor commercial-friendly, positive, and non-controversial content. You penalize profanity, negativity, and controversial topics.",
        "user_template": """Evaluate this audio segment from an advertiser/brand safety perspective:

Text: "{text}"
Topic: {topic}
Tone: {tone}

Rate this segment on a scale of 1-5 (5 being brand-safe) and provide:
1. score (1-5)
2. opinion (brief assessment from advertiser perspective)
3. rationale (why you gave this score)
4. confidence (0.0-1.0, how confident you are in this rating)

Respond ONLY with JSON:
{{"score": <number>, "opinion": "<text>", "rationale": "<text>", "confidence": <number>}}"""
    }
}

def call_langflow_chain(flow_name: str, segment: dict) -> dict:
    """
    Evaluates a segment using Azure GPT-4o-mini (replacing Langflow).
    Returns structured feedback including score, opinion, rationale, and confidence.

    Args:
        flow_name: Name of the evaluation chain (e.g., "genz_chain", "advertiser_chain")
        segment: Dict with segment data (text, topic, tone)

    Returns:
        Dict with score, opinion, rationale, and confidence

    Raises:
        ValueError: if response is malformed or missing fields
        Exception: for other API errors
    """
    if flow_name not in PERSONA_PROMPTS:
        raise ValueError(f"Unknown flow name: {flow_name}. Available: {list(PERSONA_PROMPTS.keys())}")
    
    prompt_config = PERSONA_PROMPTS[flow_name]
    
    # Extract segment data
    if isinstance(segment, str):
        segment = json.loads(segment)
    
    text = segment.get("text", "")
    topic = segment.get("topic", "Unknown")
    tone = segment.get("tone", "Neutral")
    
    # Format user prompt
    user_prompt = prompt_config["user_template"].format(
        text=text,
        topic=topic,
        tone=tone
    )
    
    try:
        client = AzureOpenAI(
            api_key=AZURE_GPT_KEY,
            api_version=AZURE_GPT_API_VERSION,
            azure_endpoint=AZURE_GPT_ENDPOINT
        )
        
        response = client.chat.completions.create(
            model=AZURE_GPT_DEPLOYMENT,
            messages=[
                {"role": "system", "content": prompt_config["system"]},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        data = json.loads(result_text)
        
        # Validate required fields
        required_fields = ["score", "opinion", "rationale", "confidence"]
        if not all(field in data for field in required_fields):
            raise ValueError(f"Missing expected fields in response. Got: {data.keys()}")

        # Validate score and confidence
        if not (1 <= data["score"] <= 5):
            raise ValueError(f"Score out of expected range (1–5), got: {data['score']}")
        if not isinstance(data["confidence"], (float, int)) or not (0 <= data["confidence"] <= 1):
            raise ValueError(f"Confidence must be 0.0-1.0, got: {data['confidence']}")

        return data

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {result_text}")
    except Exception as e:
        raise Exception(f"Azure OpenAI request failed: {e}")
