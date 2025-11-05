import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Azure Whisper file size limit
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Target chunk size (slightly under limit for safety)
TARGET_CHUNK_SIZE_MB = 20
TARGET_CHUNK_SIZE_BYTES = TARGET_CHUNK_SIZE_MB * 1024 * 1024

class AudioChunk:
    """Represents a chunk of audio with metadata"""
    def __init__(self, file_path: str, start_time: float, duration: float, chunk_index: int):
        self.file_path = file_path
        self.start_time = start_time
        self.duration = duration
        self.chunk_index = chunk_index

def get_audio_info(file_path: str) -> Dict:
    """Get audio file metadata using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception(f"ffprobe failed: {result.stderr}")
        
        import json
        data = json.loads(result.stdout)
        
        # Extract audio stream info
        audio_stream = next((s for s in data.get('streams', []) if s['codec_type'] == 'audio'), None)
        if not audio_stream:
            raise Exception("No audio stream found")
        
        duration = float(data['format'].get('duration', 0))
        size = int(data['format'].get('size', 0))
        
        return {
            'duration': duration,
            'size': size,
            'codec': audio_stream.get('codec_name'),
            'sample_rate': int(audio_stream.get('sample_rate', 0)),
            'channels': int(audio_stream.get('channels', 0))
        }
    except Exception as e:
        logger.error(f"Failed to get audio info: {e}")
        raise

def compress_audio(input_path: str, output_path: str) -> None:
    """Compress audio to 16kHz mono FLAC format"""
    try:
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',       # Mono
            '-c:a', 'flac',   # FLAC codec (lossless compression)
            '-y',             # Overwrite output
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"ffmpeg compression failed: {result.stderr}")
        
        logger.info(f"Compressed audio: {input_path} -> {output_path}")
    except Exception as e:
        logger.error(f"Failed to compress audio: {e}")
        raise

def chunk_audio(input_path: str, chunk_duration: float, output_dir: str) -> List[AudioChunk]:
    """Split audio into time-based chunks"""
    try:
        # Get total duration
        info = get_audio_info(input_path)
        total_duration = info['duration']
        
        chunks = []
        current_time = 0.0
        chunk_index = 0
        
        while current_time < total_duration:
            # Calculate this chunk's duration
            remaining = total_duration - current_time
            duration = min(chunk_duration, remaining)
            
            # Output path for this chunk
            output_path = os.path.join(output_dir, f"chunk_{chunk_index:04d}.flac")
            
            # Extract chunk using ffmpeg
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-ss', str(current_time),
                '-t', str(duration),
                '-ar', '16000',
                '-ac', '1',
                '-c:a', 'flac',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg chunking failed: {result.stderr}")
            
            # Create chunk metadata
            chunk = AudioChunk(
                file_path=output_path,
                start_time=current_time,
                duration=duration,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
            
            logger.info(f"Created chunk {chunk_index}: {current_time:.2f}s - {current_time + duration:.2f}s")
            
            current_time += duration
            chunk_index += 1
        
        return chunks
    except Exception as e:
        logger.error(f"Failed to chunk audio: {e}")
        raise

def process_large_audio(file_bytes: bytes, audio_id: str) -> List[AudioChunk]:
    """
    Process large audio files for Azure Whisper transcription.
    
    Strategy:
    1. Check file size
    2. If >25MB, compress to 16kHz mono FLAC
    3. If still >25MB, chunk into ~4 minute segments
    4. Return list of AudioChunk objects ready for transcription
    """
    file_size = len(file_bytes)
    logger.info(f"Processing audio file: {file_size / 1024 / 1024:.2f} MB")
    
    # Create temp directory for processing
    temp_dir = tempfile.mkdtemp(prefix=f"audio_processing_{audio_id}_")
    
    try:
        # Save original file
        original_path = os.path.join(temp_dir, "original.wav")
        with open(original_path, 'wb') as f:
            f.write(file_bytes)
        
        # Get audio info
        info = get_audio_info(original_path)
        logger.info(f"Audio info: duration={info['duration']:.2f}s, codec={info['codec']}, "
                   f"sample_rate={info['sample_rate']}, channels={info['channels']}")
        
        # If file is small enough, return single chunk
        if file_size <= MAX_FILE_SIZE_BYTES:
            logger.info("File size OK, no processing needed")
            chunk = AudioChunk(
                file_path=original_path,
                start_time=0.0,
                duration=info['duration'],
                chunk_index=0
            )
            return [chunk]
        
        # Step 1: Compress to 16kHz mono FLAC
        compressed_path = os.path.join(temp_dir, "compressed.flac")
        compress_audio(original_path, compressed_path)
        
        # Check compressed size
        compressed_size = os.path.getsize(compressed_path)
        logger.info(f"Compressed size: {compressed_size / 1024 / 1024:.2f} MB "
                   f"(reduction: {(1 - compressed_size / file_size) * 100:.1f}%)")
        
        # If compressed file is small enough, return single chunk
        if compressed_size <= MAX_FILE_SIZE_BYTES:
            logger.info("Compressed file size OK")
            chunk = AudioChunk(
                file_path=compressed_path,
                start_time=0.0,
                duration=info['duration'],
                chunk_index=0
            )
            return [chunk]
        
        # Step 2: Chunk into segments
        # Calculate chunk duration to target ~20MB chunks
        # Estimate: 16kHz mono FLAC ≈ ~80KB/second
        estimated_bitrate = compressed_size / info['duration']  # bytes per second
        chunk_duration = (TARGET_CHUNK_SIZE_BYTES / estimated_bitrate) * 0.9  # 90% safety margin
        chunk_duration = max(60, min(chunk_duration, 300))  # Between 1-5 minutes
        
        logger.info(f"Chunking audio into ~{chunk_duration:.0f}s segments")
        chunks = chunk_audio(compressed_path, chunk_duration, temp_dir)
        
        logger.info(f"Created {len(chunks)} chunks for transcription")
        return chunks
        
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        # Clean up temp directory on error
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
