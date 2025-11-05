from fastapi import APIRouter, HTTPException
from app.utils.segments import extract_segments
from app.services.cache import redis_conn
from app.config.personas import get_all_personas
import json

router = APIRouter()

@router.get("/segments/{audio_id}")
async def get_segments(audio_id: str):
    """
    Get enriched segments with transcript, classification, and persona feedback.
    
    Persona feedback is dynamically fetched for all registered personas.
    Redis key pattern: persona_feedback:{persona_id}:{audio_id}:{segment_id}
    """
    transcript_raw = redis_conn.get(f"transcript_segments:{audio_id}")
    classifier_raw = redis_conn.get(f"classifier_output:{audio_id}")

    if not transcript_raw or not classifier_raw:
        raise HTTPException(status_code=404, detail="Transcript or classifier data not found.")

    transcript_segments = json.loads(transcript_raw)
    classifier_results = json.loads(classifier_raw)
    
    # Dynamically fetch persona feedback for each segment
    personas = get_all_personas()
    persona_feedback_list = []
    
    for i in range(len(transcript_segments)):
        segment_feedback = {}
        
        # Fetch feedback from all registered personas
        for persona in personas:
            persona_id = persona["id"]
            feedback_key = f"persona_feedback:{persona_id}:{audio_id}:{i}"
            feedback_data = redis_conn.get(feedback_key)
            if feedback_data:
                segment_feedback[persona_id] = json.loads(feedback_data)
        
        persona_feedback_list.append(segment_feedback)

    enriched_segments = extract_segments(transcript_segments, classifier_results, persona_feedback_list)
    
    # Cache the enriched result
    redis_conn.set(f"segments:{audio_id}", json.dumps(enriched_segments), ex=86400)

    return {
        "audio_id": audio_id,
        "segments": enriched_segments
    }
