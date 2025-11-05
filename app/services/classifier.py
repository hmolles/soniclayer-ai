import os
from openai import AzureOpenAI

# Azure GPT-4o-mini configuration
AZURE_GPT_ENDPOINT = "https://hf2025-soniclayerai.cognitiveservices.azure.com"
AZURE_GPT_KEY = os.getenv("AZURE_GPT_KEY")
AZURE_GPT_DEPLOYMENT = "gpt-4o-mini"
AZURE_GPT_API_VERSION = "2025-01-01-preview"

TOPIC_LABELS = 
["Health",
 "Entertainment",
 "Politics",
 "Technology",
 "Food",
 "Education",
 "Environment",
 "Science",
 "Business & Finance",
 "Sports",
 "Travel",
 "Lifestyle",
 "Culture & Arts",
 "Crime & Law",
 "Weather & Climate",
 "Community & Local",
 "International Affairs",
 "Advertising & Marketing",
 "Religion & Spirituality",
 "Opinion & Editorial"
]
TONE_LABELS = [
 "Informative",
 "Humorous",
 "Excited",
 "Neutral",
 "Controversial",
 "Serious",
 "Positive / Uplifting",
 "Negative / Concerned",
 "Sarcastic",
 "Emotional / Heartfelt",
 "Inspirational",
 "Dramatic",
 "Cautious / Reserved",
 "Analytical",
 "Casual / Conversational"
]

def classify_segment(text: str) -> dict:
    """Classify a text segment using Azure GPT-4o-mini."""
    client = AzureOpenAI(
        api_key=AZURE_GPT_KEY,
        api_version=AZURE_GPT_API_VERSION,
        azure_endpoint=AZURE_GPT_ENDPOINT
    )
    
    prompt = f"""You are a content classifier. Analyze the following text and classify it.

Text: "{text}"

Classify the text into:
1. Topic - Choose ONE from: {', '.join(TOPIC_LABELS)}
2. Tone - Choose ONE from: {', '.join(TONE_LABELS)}

Respond in JSON format:
{{"topic": "chosen_topic", "tone": "chosen_tone"}}

Only return the JSON, no other text."""
    
    try:
        response = client.chat.completions.create(
            model=AZURE_GPT_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful content classification assistant. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        result = json.loads(result_text)
        
        # Validate and return
        return {
            "topic": result.get("topic", "Entertainment"),
            "tone": result.get("tone", "Neutral")
        }
    except Exception as e:
        print(f"Classification error: {e}")
        # Return defaults on error
        return {
            "topic": "Entertainment",
            "tone": "Neutral"
        }

def classify_transcript_segments(segments: list) -> list:
    """Classify all transcript segments."""
    return [classify_segment(seg["text"]) for seg in segments]
