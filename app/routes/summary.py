from fastapi import APIRouter, HTTPException
from app.services.cache import redis_conn
from app.services.summary_aggregator import aggregate_persona_feedback
from app.config.personas import get_all_personas
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary/{audio_id}")
async def get_audio_summary(audio_id: str):
    """
    Get aggregated summary statistics for all personas
    
    Returns:
        {
            "audio_id": "test1",
            "num_segments": 18,
            "personas": {
                "genz_teen": {
                    "avg_score": 3.2,
                    "score_distribution": {"1": 1, "2": 3, "3": 5, "4": 6, "5": 3},
                    "avg_confidence": 0.75,
                    "top_segments": [5, 12, 7],
                    "worst_segments": [2, 9]
                },
                "advertiser": {...},
                ...
            }
        }
    """
    # Check cache first (24-hour TTL)
    cache_key = f"audio_summary:{audio_id}"
    cached_summary = redis_conn.get(cache_key)
    
    if cached_summary:
        logger.info(f"Cache hit for audio summary: {audio_id}")
        return json.loads(cached_summary)
    
    # Get number of segments from transcript data
    transcript_raw = redis_conn.get(f"transcript_segments:{audio_id}")
    
    if not transcript_raw:
        raise HTTPException(status_code=404, detail=f"Audio {audio_id} not found")
    
    transcript_segments = json.loads(transcript_raw)
    num_segments = len(transcript_segments)
    
    # Aggregate feedback for all personas
    personas = get_all_personas()
    persona_summaries = {}
    
    for persona in personas:
        persona_id = persona["id"]
        
        try:
            summary = aggregate_persona_feedback(audio_id, persona_id, num_segments)
            persona_summaries[persona_id] = summary
        
        except Exception as e:
            logger.error(f"Error aggregating feedback for persona {persona_id}: {e}")
            # Include placeholder for failed personas
            persona_summaries[persona_id] = {
                "avg_score": 0,
                "score_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
                "avg_confidence": 0,
                "top_segments": [],
                "worst_segments": [],
                "error": str(e)
            }
    
    result = {
        "audio_id": audio_id,
        "num_segments": num_segments,
        "personas": persona_summaries
    }
    
    # Cache the result with 24-hour TTL (86400 seconds)
    redis_conn.set(cache_key, json.dumps(result), ex=86400)
    logger.info(f"Cached audio summary for {audio_id}")
    
    return result
