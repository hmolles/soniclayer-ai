import json
import logging
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from rq import Queue
from app.services.langflow_client import call_langflow_chain
from app.services.transcryption import transcribe_audio, transcribe_audio_with_timestamps
from app.services.classifier import classify_segment
from app.services.cache import redis_conn
from app.utils.hashing import generate_audio_hash
from app.utils.segmentation import segment_transcript
from app.workers.genz_worker import process_transcript as genz_process
from app.workers.advertiser_worker import process_transcript as advertiser_process

router = APIRouter()
logger = logging.getLogger(__name__)

# Create RQ queue for background tasks
queue = Queue("transcript_tasks", connection=redis_conn)

# Ensure uploads directory exists
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

@router.post("/evaluate/")
async def evaluate_audio(file: UploadFile):
    """
    Upload audio file, transcribe, classify, and queue persona evaluation tasks.
    
    Returns:
        - audio_id: Unique hash identifier for the audio
        - status: Processing status
        - job_ids: RQ job IDs for tracking
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload an audio file (WAV recommended)."
            )
        
        # Read file bytes
        audio_bytes = await file.read()
        
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Generate unique audio ID from file hash
        audio_id = generate_audio_hash(audio_bytes)
        
        # Check if this audio was already processed (deduplication)
        existing_segments = redis_conn.get(f"transcript_segments:{audio_id}")
        if existing_segments:
            logger.info(f"Audio {audio_id} already processed, returning cached results")
            return JSONResponse({
                "audio_id": audio_id,
                "status": "already_processed",
                "message": "This audio has already been processed. Use /segments/{audio_id} to retrieve results."
            })
        
        # Save audio file to uploads directory
        audio_path = UPLOADS_DIR / f"{audio_id}.wav"
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        logger.info(f"Audio saved: {audio_path} ({len(audio_bytes)} bytes)")
        
        # Step 1: Transcribe audio using Whisper with accurate timestamps
        try:
            transcript_segments = transcribe_audio_with_timestamps(audio_bytes, segment_duration=15.0)
            logger.info(f"Transcription complete: {len(transcript_segments)} segments with timestamps")
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {str(e)}"
            )
        
        # Note: transcript_segments now already has start, end, and text from Whisper
        # No need for manual segmentation
        logger.info(f"Created {len(transcript_segments)} segments with accurate timestamps")
        
        # Step 2: Classify each segment (topic and tone)
        classifier_results = []
        for idx, segment in enumerate(transcript_segments):
            try:
                classification = classify_segment(segment["text"])
                classifier_results.append({
                    "segment_id": idx,
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"],
                    "topic": classification.get("topic", "Unknown"),
                    "tone": classification.get("tone", "Unknown"),
                    "tags": classification.get("tags", [])
                })
            except Exception as e:
                logger.error(f"Classification failed for segment {idx}: {e}")
                classifier_results.append({
                    "segment_id": idx,
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"],
                    "topic": "Unknown",
                    "tone": "Unknown",
                    "tags": [],
                    "error": str(e)
                })
        
        # Step 4: Store transcript segments and classifier output in Redis
        redis_conn.set(
            f"transcript_segments:{audio_id}",
            json.dumps(transcript_segments),
            ex=86400  # 24-hour TTL
        )
        
        redis_conn.set(
            f"classifier_output:{audio_id}",
            json.dumps(classifier_results),
            ex=86400  # 24-hour TTL
        )
        
        logger.info(f"Stored transcript and classification in Redis for {audio_id}")
        
        # Step 5: Queue persona evaluation workers (GenZ and Advertiser for MVP)
        job_ids = {}
        
        try:
            # Queue GenZ worker
            genz_job = queue.enqueue(
                genz_process,
                audio_id,
                transcript_segments,
                classifier_results,
                job_timeout="10m"
            )
            job_ids["genz"] = genz_job.id
            logger.info(f"Queued GenZ worker: {genz_job.id}")
        except Exception as e:
            logger.error(f"Failed to queue GenZ worker: {e}")
            job_ids["genz"] = f"error: {str(e)}"
        
        try:
            # Queue Advertiser worker
            advertiser_job = queue.enqueue(
                advertiser_process,
                audio_id,
                transcript_segments,
                classifier_results,
                job_timeout="10m"
            )
            job_ids["advertiser"] = advertiser_job.id
            logger.info(f"Queued Advertiser worker: {advertiser_job.id}")
        except Exception as e:
            logger.error(f"Failed to queue Advertiser worker: {e}")
            job_ids["advertiser"] = f"error: {str(e)}"
        
        # Step 6: Return response with audio_id and job tracking info
        total_transcript_length = sum(len(seg["text"]) for seg in transcript_segments)
        return JSONResponse({
            "audio_id": audio_id,
            "status": "processing",
            "transcript_length": total_transcript_length,
            "segment_count": len(transcript_segments),
            "job_ids": job_ids,
            "message": f"Audio uploaded successfully. {len(transcript_segments)} segments are being processed by persona agents."
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /evaluate/: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
