"""Utility functions for scanning and managing audio files."""
import os
from pathlib import Path
from datetime import datetime
import requests


def get_audio_summary_mini(audio_id: str) -> dict:
    """
    Fetch mini summary (just persona scores) from backend.
    
    Args:
        audio_id: Audio file identifier
    
    Returns:
        Dict mapping persona_id to mini stats:
        {
            "genz": {"avg_score": 2.8, "emoji": "🔥"},
            "advertiser": {"avg_score": 4.2, "emoji": "💼"}
        }
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from personas_config import get_all_personas
    
    try:
        response = requests.get(f"http://localhost:8000/summary/{audio_id}", timeout=2)
        if response.status_code == 200:
            summary_data = response.json()
            
            # Build mini summary
            mini_summary = {}
            personas = get_all_personas()
            
            for persona in personas:
                persona_id = persona["id"]
                if persona_id in summary_data.get("personas", {}):
                    stats = summary_data["personas"][persona_id]
                    mini_summary[persona_id] = {
                        "avg_score": stats.get("avg_score", 0),
                        "emoji": persona["emoji"]
                    }
            
            return mini_summary
    except Exception as e:
        # Log but don't break - fallback to empty summary
        print(f"Warning: Could not fetch summary for {audio_id}: {e}")
    
    return {}


def get_all_audio_files():
    """
    Scan uploads folder and return list of audio files with metadata.
    
    Returns:
        List of dicts with audio metadata:
        [
            {
                "audio_id": "50f53153...",
                "filename": "50f53153....wav",
                "display_name": "original_upload.wav",  # Original filename if available
                "file_size_mb": 12.5,
                "upload_date": "2025-11-05 10:30",
                "num_segments": 18,
                "summary": {"genz": {"avg_score": 2.8, "emoji": "🔥"}, ...}
            }
        ]
    """
    import sys
    from pathlib import Path as SysPath
    sys.path.insert(0, str(SysPath(__file__).parent.parent.parent / "app"))
    from services.cache import redis_conn
    
    uploads_dir = Path("uploads")
    
    if not uploads_dir.exists():
        return []
    
    audio_files = []
    
    for file_path in uploads_dir.glob("*.wav"):
        try:
            # Get file stats
            stats = file_path.stat()
            file_size_mb = round(stats.st_size / (1024 * 1024), 2)
            upload_date = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
            
            # Extract audio_id (filename without extension)
            audio_id = file_path.stem
            
            # Try to fetch original filename from Redis
            original_name = redis_conn.get(f"original_filename:{audio_id}")
            if original_name:
                display_name = original_name.decode('utf-8') if isinstance(original_name, bytes) else original_name
            else:
                # Fallback to truncated hash
                display_name = f"{audio_id[:12]}..." if len(audio_id) > 12 else audio_id
            
            # Try to get number of segments from backend
            num_segments = get_segment_count(audio_id)
            
            # Fetch summary data (ONCE per scan)
            summary = get_audio_summary_mini(audio_id)
            
            audio_files.append({
                "audio_id": audio_id,
                "filename": file_path.name,
                "display_name": display_name,
                "file_size_mb": file_size_mb,
                "upload_date": upload_date,
                "num_segments": num_segments,
                "summary": summary
            })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    # Sort by upload date (newest first)
    audio_files.sort(key=lambda x: x["upload_date"], reverse=True)
    
    return audio_files


def get_segment_count(audio_id: str) -> int:
    """
    Get number of segments for an audio file from backend.
    
    Args:
        audio_id: Audio file identifier
        
    Returns:
        Number of segments, or 0 if unavailable
    """
    try:
        response = requests.get(f"http://localhost:8000/segments/{audio_id}", timeout=2)
        if response.status_code == 200:
            segments = response.json()
            return len(segments)
    except:
        pass
    
    return 0


def get_audio_metadata(audio_id: str) -> dict:
    """
    Get detailed metadata for a specific audio file.
    
    Args:
        audio_id: Audio file identifier
        
    Returns:
        Dict with metadata or None if not found
    """
    audio_files = get_all_audio_files()
    
    for audio in audio_files:
        if audio["audio_id"] == audio_id:
            return audio
    
    return None
