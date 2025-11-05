import json
from app.services.cache import redis_conn
from app.utils.hashing import generate_audio_hash


def process_transcript(transcript_text, transcript_segments, classifier_results):
    """
    Process transcript segments for Parents persona.
    Note: This worker does not yet use a PersonaAgent subclass.
    TODO: Create ParentsAgent and refactor this worker.
    """
    feedback = []
    for i, segment in enumerate(transcript_segments):
        score = 0.0
        topic = classifier_results[i]["topic"]
        tone = classifier_results[i]["tone"]

        if topic.lower() in ["health", "education"]: 
            score += 0.4
        if tone == "informative": 
            score += 0.2
        if "profanity" in segment.get("text", "").lower(): 
            score -= 0.6

        feedback.append({"parents": round(max(min(score, 5), 0))})

    # Store feedback in Redis
    audio_hash = generate_audio_hash(transcript_text.encode())
    redis_conn.set(
        f"persona_feedback:parents:{audio_hash}",
        json.dumps(feedback),
        ex=86400
    )
    
    return feedback
