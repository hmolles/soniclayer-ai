from transformers import pipeline

# Load zero-shot classification pipelines
topic_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
tone_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

TOPIC_LABELS = ["Health", "Entertainment", "Politics", "Technology", "Food", "Education"]
TONE_LABELS = ["Informative", "Humorous", "Excited", "Neutral", "Controversial"]

def classify_segment(text: str) -> dict:
    topic_result = topic_classifier(text, TOPIC_LABELS)
    tone_result = tone_classifier(text, TONE_LABELS)

    return {
        "topic": topic_result["labels"][0],
        "tone": tone_result["labels"][0]
    }

def classify_transcript_segments(segments: list) -> list:
    return [classify_segment(seg["text"]) for seg in segments]