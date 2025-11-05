import os
import tempfile
import time
import logging
from typing import List, Dict
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

# Azure Whisper configuration
AZURE_WHISPER_ENDPOINT = "https://admin-mhlg381w-northcentralus.cognitiveservices.azure.com"
AZURE_WHISPER_KEY = os.getenv("AZURE_WHISPER_KEY")
AZURE_WHISPER_API_VERSION = "2024-02-01"  # Updated to stable version
AZURE_WHISPER_DEPLOYMENT_NAME = "whisper"  # Deployment name from Azure

# Rate limiting: 3 requests per minute
RATE_LIMIT_REQUESTS = 3
RATE_LIMIT_PERIOD = 60  # seconds
last_request_times = []

def _wait_for_rate_limit():
    """Enforce rate limiting of 3 requests per minute."""
    global last_request_times
    current_time = time.time()
    
    # Remove timestamps older than the rate limit period
    last_request_times = [t for t in last_request_times if current_time - t < RATE_LIMIT_PERIOD]
    
    # If we've hit the limit, wait
    if len(last_request_times) >= RATE_LIMIT_REQUESTS:
        sleep_time = RATE_LIMIT_PERIOD - (current_time - last_request_times[0]) + 1
        if sleep_time > 0:
            print(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
            last_request_times.clear()
    
    # Record this request
    last_request_times.append(time.time())

def transcribe_audio(file_bytes: bytes) -> str:
    """Basic transcription returning only text using Azure Whisper API."""
    _wait_for_rate_limit()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        client = AzureOpenAI(
            api_key=AZURE_WHISPER_KEY,
            api_version=AZURE_WHISPER_API_VERSION,
            azure_endpoint=AZURE_WHISPER_ENDPOINT
        )
        
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=AZURE_WHISPER_DEPLOYMENT_NAME,
                file=audio_file
            )
        
        return result.text.strip()
    finally:
        os.remove(tmp_path)

def transcribe_audio_with_timestamps(file_bytes: bytes, segment_duration: float = 15.0) -> list:
    """
    Transcribe audio and return segments with timestamps using Azure Whisper API.
    Note: Azure Whisper API returns segments but not word-level timestamps in the same way
    as local Whisper. We'll create segments based on the returned segments.
    """
    _wait_for_rate_limit()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        client = AzureOpenAI(
            api_key=AZURE_WHISPER_KEY,
            api_version=AZURE_WHISPER_API_VERSION,
            azure_endpoint=AZURE_WHISPER_ENDPOINT
        )
        
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=AZURE_WHISPER_DEPLOYMENT_NAME,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        # Process Azure Whisper segments
        segments = []
        current_segment = {
            "start": 0.0,
            "text": "",
        }
        
        # Iterate through Azure Whisper's segments
        for whisper_segment in result.segments:
            segment_start = whisper_segment.start if hasattr(whisper_segment, 'start') else 0.0
            segment_end = whisper_segment.end if hasattr(whisper_segment, 'end') else (segment_start + segment_duration)
            segment_text = whisper_segment.text.strip() if hasattr(whisper_segment, 'text') else ""
            
            # If adding this text would exceed our target duration, finalize current segment
            if current_segment["text"] and (segment_end - current_segment["start"]) > segment_duration:
                segments.append({
                    "start": round(current_segment["start"], 2),
                    "end": round(segment_start, 2),
                    "text": current_segment["text"].strip()
                })
                # Start new segment
                current_segment = {
                    "start": segment_start,
                    "text": segment_text,
                }
            else:
                # Add to current segment
                if current_segment["text"]:
                    current_segment["text"] += " " + segment_text
                else:
                    current_segment["text"] = segment_text
                    current_segment["start"] = segment_start
        
        # Add final segment
        if current_segment["text"]:
            last_segment = result.segments[-1] if result.segments else None
            current_segment["end"] = last_segment.end if (last_segment and hasattr(last_segment, 'end')) else (current_segment["start"] + segment_duration)
            segments.append({
                "start": round(current_segment["start"], 2),
                "end": round(current_segment["end"], 2),
                "text": current_segment["text"].strip()
            })
        
        return segments
    finally:
        os.remove(tmp_path)

def transcribe_chunk(chunk_path: str, chunk_start_time: float) -> List[Dict]:
    """
    Transcribe a single audio chunk and return segments with adjusted timestamps.
    
    Args:
        chunk_path: Path to the audio chunk file
        chunk_start_time: Start time offset of this chunk in the original audio
    
    Returns:
        List of segments with timestamps adjusted for the chunk's position
    """
    _wait_for_rate_limit()
    
    try:
        client = AzureOpenAI(
            api_key=AZURE_WHISPER_KEY,
            api_version=AZURE_WHISPER_API_VERSION,
            azure_endpoint=AZURE_WHISPER_ENDPOINT
        )
        
        with open(chunk_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model=AZURE_WHISPER_DEPLOYMENT_NAME,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        # Process segments and adjust timestamps
        segments = []
        for whisper_segment in result.segments:
            segment_start = whisper_segment.start if hasattr(whisper_segment, 'start') else 0.0
            segment_end = whisper_segment.end if hasattr(whisper_segment, 'end') else segment_start
            segment_text = whisper_segment.text.strip() if hasattr(whisper_segment, 'text') else ""
            
            if segment_text:
                segments.append({
                    "start": round(chunk_start_time + segment_start, 2),
                    "end": round(chunk_start_time + segment_end, 2),
                    "text": segment_text
                })
        
        return segments
    except Exception as e:
        logger.error(f"Failed to transcribe chunk at {chunk_start_time}s: {e}")
        raise

def transcribe_chunked_audio(chunks: List) -> List[Dict]:
    """
    Transcribe multiple audio chunks and stitch results with continuous timestamps.
    
    Args:
        chunks: List of AudioChunk objects from media_processor
    
    Returns:
        List of segments with continuous timestamps across all chunks
    """
    all_segments = []
    
    logger.info(f"Transcribing {len(chunks)} audio chunks...")
    
    for chunk in chunks:
        logger.info(f"Transcribing chunk {chunk.chunk_index} (start: {chunk.start_time}s, duration: {chunk.duration:.2f}s)")
        
        try:
            chunk_segments = transcribe_chunk(chunk.file_path, chunk.start_time)
            all_segments.extend(chunk_segments)
            logger.info(f"Chunk {chunk.chunk_index}: {len(chunk_segments)} segments transcribed")
        except Exception as e:
            logger.error(f"Failed to transcribe chunk {chunk.chunk_index}: {e}")
            raise Exception(f"Chunk {chunk.chunk_index} transcription failed: {str(e)}")
    
    # Merge adjacent segments with target duration
    merged_segments = merge_segments(all_segments, target_duration=15.0)
    
    logger.info(f"Transcription complete: {len(merged_segments)} final segments from {len(all_segments)} raw segments")
    return merged_segments

def merge_segments(segments: List[Dict], target_duration: float = 15.0) -> List[Dict]:
    """
    Merge short segments into larger ones of approximately target_duration.
    
    Args:
        segments: List of segments with start, end, and text
        target_duration: Target duration for merged segments in seconds
    
    Returns:
        List of merged segments
    """
    if not segments:
        return []
    
    merged = []
    current = {
        "start": segments[0]["start"],
        "end": segments[0]["end"],
        "text": segments[0]["text"]
    }
    
    for segment in segments[1:]:
        current_duration = current["end"] - current["start"]
        
        # If adding this segment would exceed target duration, finalize current
        if current_duration >= target_duration:
            merged.append(current)
            current = {
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"]
            }
        else:
            # Merge with current segment
            current["end"] = segment["end"]
            current["text"] += " " + segment["text"]
    
    # Add final segment
    if current["text"]:
        merged.append(current)
    
    return merged
