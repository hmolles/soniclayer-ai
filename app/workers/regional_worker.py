import json
from app.services.cache import redis_conn
from app.utils.hashing import generate_audio_hash


def process_transcript(transcript_text, transcript_segments, classifier_results):
    """
    Process transcript segments for Regional persona.
    Note: This worker does not yet use a PersonaAgent subclass.
    TODO: Create RegionalAgent and refactor this worker.
    """
    feedback = []
    for i, segment in enumerate(transcript_segments):
        score = 0.0
        topic = classifier_results[i]["topic"]
        tone = classifier_results[i]["tone"]

        if "regional" in topic.lower() or "community" in topic.lower(): 
            score += 0.5
        if tone == "clear": 
            score += 0.2
        if tone == "fast-paced": 
            score -= 0.3

        feedback.append({"regional": round(max(min(score, 5), 0))})

    # Store feedback in Redis
    audio_hash = generate_audio_hash(transcript_text.encode())
    redis_conn.set(
        f"persona_feedback:regional:{audio_hash}",
        json.dumps(feedback),
        ex=86400
    )
    
    return feedback
