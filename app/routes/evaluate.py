import json
import logging
import os
import shutil
import importlib
from pathlib import Path
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from rq import Queue
from app.services.langflow_client import call_langflow_chain
from app.services.transcryption import transcribe_audio, transcribe_audio_with_timestamps, transcribe_chunked_audio
from app.services.media_processor import process_large_audio
from app.services.classifier import classify_segment
from app.services.cache import redis_conn
from app.utils.hashing import generate_audio_hash
from app.utils.segmentation import segment_transcript
from app.config.personas import get_all_personas

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
    Handles large files (>25MB) via compression and chunking.
    
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
        
        # Store original filename for UI display
        if file.filename:
            redis_conn.set(f"original_filename:{audio_id}", file.filename, ex=86400)  # 24h TTL
        
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
        
        file_size_mb = len(audio_bytes) / (1024 * 1024)
        logger.info(f"Audio saved: {audio_path} ({file_size_mb:.2f} MB)")
        
        # Step 1: Process and transcribe audio (handles large files via chunking)
        try:
            # Process audio file (compress/chunk if needed)
            chunks = process_large_audio(audio_bytes, audio_id)
            logger.info(f"Audio processing complete: {len(chunks)} chunk(s) to transcribe")
            
            try:
                # Transcribe chunks with rate limiting and timestamp stitching
                if len(chunks) == 1:
                    # Single chunk - read compressed audio and use standard transcription
                    logger.info("Single chunk, using standard transcription with compressed audio")
                    with open(chunks[0].file_path, "rb") as f:
                        compressed_audio = f.read()
                    transcript_segments = transcribe_audio_with_timestamps(compressed_audio, segment_duration=15.0)
                else:
                    # Multiple chunks - use chunked transcription
                    logger.info(f"Multiple chunks ({len(chunks)}), using chunked transcription with rate limiting")
                    transcript_segments = transcribe_chunked_audio(chunks)
                
                logger.info(f"Transcription complete: {len(transcript_segments)} segments with timestamps")
            finally:
                # Clean up temporary chunk files
                for chunk in chunks:
                    chunk_dir = os.path.dirname(chunk.file_path)
                    if chunk_dir and os.path.exists(chunk_dir) and "audio_processing_" in chunk_dir:
                        shutil.rmtree(chunk_dir, ignore_errors=True)
                        logger.debug(f"Cleaned up temp directory: {chunk_dir}")
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {str(e)}"
            )
        
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
        
        # Step 3: Store transcript segments and classifier output in Redis
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
        
        # Step 4: Dynamically queue all persona evaluation workers
        job_ids = {}
        personas = get_all_personas()
        
        for persona in personas:
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
                logger.info(f"Queued {persona['display_name']} worker: {job.id}")
            except Exception as e:
                logger.error(f"Failed to queue {persona['display_name']} worker: {e}")
                job_ids[persona_id] = f"error: {str(e)}"
        
        # Step 5: Return response with audio_id and job tracking info
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
