import json
import logging
import importlib
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from rq import Queue
from app.services.cache import redis_conn
from app.config.personas import get_all_personas

router = APIRouter()
logger = logging.getLogger(__name__)

# Create RQ queue for background tasks
queue = Queue("transcript_tasks", connection=redis_conn)

@router.post("/re-evaluate/{audio_id}")
async def re_evaluate_audio(audio_id: str, persona_ids: list[str] = None):
    """
    Re-evaluate an already-processed audio file with specific personas.
    Useful after editing persona prompts to see updated evaluations.
    
    Args:
        audio_id: Hash identifier for the audio
        persona_ids: Optional list of persona IDs to re-evaluate (if None, re-evaluates all)
    
    Returns:
        - audio_id: Audio identifier
        - status: Re-evaluation status
        - job_ids: RQ job IDs for tracking
        - personas_queued: Number of personas queued for evaluation
    """
    try:
        # Check if audio exists in Redis
        transcript_segments_raw = redis_conn.get(f"transcript_segments:{audio_id}")
        classifier_output_raw = redis_conn.get(f"classifier_output:{audio_id}")
        
        if not transcript_segments_raw or not classifier_output_raw:
            raise HTTPException(
                status_code=404,
                detail=f"Audio {audio_id} not found. Please upload and process the audio first using /evaluate/"
            )
        
        # Load existing data
        transcript_segments = json.loads(transcript_segments_raw)
        classifier_results = json.loads(classifier_output_raw)
        
        logger.info(f"Re-evaluating audio {audio_id} with {len(transcript_segments)} segments")
        
        # Determine which personas to re-evaluate
        all_personas = get_all_personas()
        
        if persona_ids:
            # Re-evaluate only specified personas
            personas_to_queue = [p for p in all_personas if p["id"] in persona_ids]
            if not personas_to_queue:
                raise HTTPException(
                    status_code=400,
                    detail=f"None of the specified persona IDs found: {persona_ids}"
                )
        else:
            # Re-evaluate all personas
            personas_to_queue = all_personas
        
        # Queue persona evaluation workers
        job_ids = {}
        
        for persona in personas_to_queue:
            persona_id = persona["id"]
            worker_module = persona["worker_module"]
            
            try:
                # Dynamically import the worker module
                module = importlib.import_module(worker_module)
                process_function = getattr(module, "process_transcript")
                
                # Queue the worker
                job = queue.enqueue(
                    process_function,
                    audio_id,
                    transcript_segments,
                    classifier_results,
                    job_timeout="10m"
                )
                job_ids[persona_id] = job.id
                logger.info(f"Re-queued {persona['display_name']} worker: {job.id}")
            except Exception as e:
                logger.error(f"Failed to queue {persona['display_name']} worker: {e}")
                job_ids[persona_id] = f"error: {str(e)}"
        
        return JSONResponse({
            "audio_id": audio_id,
            "status": "re-evaluating",
            "job_ids": job_ids,
            "personas_queued": len(job_ids),
            "message": f"Re-evaluating {len(job_ids)} persona(s) on {len(transcript_segments)} segments."
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /re-evaluate/: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
