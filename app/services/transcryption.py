import whisper
import tempfile
import os

model = whisper.load_model("base")  # You can change to "small", "medium", or "large"

def transcribe_audio(file_bytes: bytes) -> str:
    """Basic transcription returning only text."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(tmp_path)
        return result["text"].strip()
    finally:
        os.remove(tmp_path)

def transcribe_audio_with_timestamps(file_bytes: bytes, segment_duration: float = 15.0) -> list:
    """
    Transcribe audio and return segments with accurate timestamps from Whisper.
    Uses Whisper's word-level timestamps to create properly aligned segments.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # Get word-level timestamps
        result = model.transcribe(tmp_path, word_timestamps=True)
        
        segments = []
        current_segment = {
            "start": 0.0,
            "text": "",
            "words": []
        }
        
        # Iterate through Whisper's segments
        for whisper_segment in result.get("segments", []):
            segment_start = whisper_segment["start"]
            segment_end = whisper_segment["end"]
            segment_text = whisper_segment["text"].strip()
            
            # If adding this text would exceed our target duration, finalize current segment
            if current_segment["text"] and (segment_end - current_segment["start"]) > segment_duration:
                current_segment["end"] = segment_start
                segments.append({
                    "start": round(current_segment["start"], 2),
                    "end": round(current_segment["end"], 2),
                    "text": current_segment["text"].strip()
                })
                # Start new segment
                current_segment = {
                    "start": segment_start,
                    "text": segment_text,
                    "words": []
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
            # Use the last timestamp from result
            last_segment = result.get("segments", [])[-1] if result.get("segments") else None
            current_segment["end"] = last_segment["end"] if last_segment else current_segment["start"] + segment_duration
            segments.append({
                "start": round(current_segment["start"], 2),
                "end": round(current_segment["end"], 2),
                "text": current_segment["text"].strip()
            })
        
        return segments
    finally:
        os.remove(tmp_path)