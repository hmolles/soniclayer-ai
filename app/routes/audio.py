from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()


@router.get("/audio/{audio_id}")
async def serve_audio(audio_id: str):
    file_path = f"uploads/{audio_id}.wav"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(file_path, media_type="audio/wav")
