import os
import tempfile
import time
from openai import AzureOpenAI

# Azure Whisper configuration
AZURE_WHISPER_ENDPOINT = "https://admin-mhlf1bll-swedencentral.cognitiveservices.azure.com/openai/deployments/whisper/audio/translations"
AZURE_WHISPER_KEY = os.getenv("AZURE_WHISPER_KEY")
AZURE_WHISPER_API_VERSION = "2024-06-01"
AZURE_WHISPER_DEPLOYMENT_NAME = "whisper"  # Deployment name from endpoint

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
            azure_endpoint=AZURE_WHISPER_ENDPOINT.rsplit("/", 3)[0]  # Get base URL
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
            azure_endpoint=AZURE_WHISPER_ENDPOINT.rsplit("/", 3)[0]  # Get base URL
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
            segment_start = whisper_segment.get("start", 0.0)
            segment_end = whisper_segment.get("end", segment_start + segment_duration)
            segment_text = whisper_segment.get("text", "").strip()
            
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
            current_segment["end"] = last_segment.get("end", current_segment["start"] + segment_duration) if last_segment else current_segment["start"] + segment_duration
            segments.append({
                "start": round(current_segment["start"], 2),
                "end": round(current_segment["end"], 2),
                "text": current_segment["text"].strip()
            })
        
        return segments
    finally:
        os.remove(tmp_path)
