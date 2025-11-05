from fastapi import APIRouter, HTTPException
from app.utils.segments import extract_segments
from app.services.cache import redis_conn
import json

router = APIRouter()

@router.get("/segments/{audio_id}")
async def get_segments(audio_id: str):
    """
    Get enriched segments with transcript, classification, and persona feedback.
    
    Persona feedback is stored per-segment in Redis as:
    - persona_feedback:genz:{audio_id}:{segment_id}
    - persona_feedback:advertiser:{audio_id}:{segment_id}
    """
    transcript_raw = redis_conn.get(f"transcript_segments:{audio_id}")
    classifier_raw = redis_conn.get(f"classifier_output:{audio_id}")

    if not transcript_raw or not classifier_raw:
        raise HTTPException(status_code=404, detail="Transcript or classifier data not found.")

    transcript_segments = json.loads(transcript_raw)
    classifier_results = json.loads(classifier_raw)
    
    # Fetch persona feedback for each segment using audio_id
    persona_feedback_list = []
    for i in range(len(transcript_segments)):
        segment_feedback = {}
        
        # Fetch GenZ feedback
        genz_key = f"persona_feedback:genz:{audio_id}:{i}"
        genz_data = redis_conn.get(genz_key)
        if genz_data:
            segment_feedback["genz"] = json.loads(genz_data)
        
        # Fetch Advertiser feedback
        advertiser_key = f"persona_feedback:advertiser:{audio_id}:{i}"
        advertiser_data = redis_conn.get(advertiser_key)
        if advertiser_data:
            segment_feedback["advertiser"] = json.loads(advertiser_data)
        
        persona_feedback_list.append(segment_feedback)

    enriched_segments = extract_segments(transcript_segments, classifier_results, persona_feedback_list)
    
    # Cache the enriched result
    redis_conn.set(f"segments:{audio_id}", json.dumps(enriched_segments), ex=86400)

    return {
        "audio_id": audio_id,
        "segments": enriched_segments
    }