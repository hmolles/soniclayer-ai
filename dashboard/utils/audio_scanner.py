"""Utility functions for scanning and managing audio files."""
import os
from pathlib import Path
from datetime import datetime
import requests


def get_all_audio_files():
    """
    Scan uploads folder and return list of audio files with metadata.
    
    Returns:
        List of dicts with audio metadata:
        [
            {
                "audio_id": "50f53153...",
                "filename": "50f53153....wav",
                "file_size_mb": 12.5,
                "upload_date": "2025-11-05 10:30",
                "num_segments": 18
            }
        ]
    """
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
            
            # Try to get number of segments from backend
            num_segments = get_segment_count(audio_id)
            
            audio_files.append({
                "audio_id": audio_id,
                "filename": file_path.name,
                "file_size_mb": file_size_mb,
                "upload_date": upload_date,
                "num_segments": num_segments
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
