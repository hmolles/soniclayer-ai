import json
import logging
from app.services.cache import redis_conn
from app.services.langflow_client import call_langflow_chain

logger = logging.getLogger(__name__)


def process_transcript(audio_id, transcript_segments, classifier_results):
    """
    Process transcript segments using GenZ Langflow chain.
    
    Args:
        audio_id: Unique audio identifier (hash of audio file)
        transcript_segments: List of segment dicts with 'text' field
        classifier_results: List of classification dicts with 'topic' and 'tone'
    """
    feedback = []
    
    for i, segment in enumerate(transcript_segments):
        segment_id = classifier_results[i].get("segment_id", i)
        
        # Build segment input for Langflow
        segment_input = json.dumps({
            "text": segment.get("text", ""),
            "topic": classifier_results[i].get("topic", ""),
            "tone": classifier_results[i].get("tone", "")
        })
        
        # Call Langflow GenZ chain
        try:
            result = call_langflow_chain("genz_chain", segment_input)
            logger.info(f"GenZ evaluation for segment {segment_id}: {result}")
        except Exception as e:
            logger.error(f"Error calling GenZ Langflow chain for segment {segment_id}: {e}")
            # Fallback to default response on error
            result = {
                "score": 3,
                "opinion": "Unable to evaluate",
                "rationale": f"Error: {str(e)}",
                "confidence": 0.0,
                "note": "Langflow call failed"
            }
        
        # Store feedback with segment ID
        feedback.append({
            "segment_id": segment_id,
            "genz": result
        })
        
        # Store individual segment feedback in Redis
        redis_conn.set(
            f"persona_feedback:genz:{audio_id}:{segment_id}",
            json.dumps(result),
            ex=86400
        )
    
    # Store aggregated feedback
    redis_conn.set(
        f"persona_feedback:genz:{audio_id}",
        json.dumps(feedback),
        ex=86400
    )
    
    return feedback
