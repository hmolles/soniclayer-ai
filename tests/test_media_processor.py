import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.services.media_processor import process_large_audio, AudioChunk, get_audio_info, compress_audio


@pytest.fixture
def mock_audio_info():
    """Mock audio info response from ffprobe."""
    return {
        'format': {
            'duration': '300.0',
            'size': '50000000'
        },
        'streams': [{
            'codec_type': 'audio',
            'sample_rate': '48000',
            'channels': 2
        }]
    }


@pytest.fixture
def small_audio_bytes():
    """Create small audio bytes (5MB simulated)."""
    return b"RIFF" + b"\x00" * (5 * 1024 * 1024)


@pytest.fixture
def large_audio_bytes():
    """Create large audio bytes (50MB simulated)."""
    return b"RIFF" + b"\x00" * (50 * 1024 * 1024)


@patch('app.services.media_processor.get_audio_info')
@patch('app.services.media_processor.compress_audio')
def test_small_audio_single_chunk(mock_compress, mock_get_info, small_audio_bytes, mock_audio_info):
    """Test that small audio files result in a single compressed chunk."""
    mock_audio_info['format']['duration'] = '60.0'
    mock_audio_info['format']['size'] = str(len(small_audio_bytes))
    mock_get_info.return_value = mock_audio_info
    
    with tempfile.NamedTemporaryFile(suffix='.flac', delete=False) as tmp:
        tmp.write(b"compressed audio")
        compressed_path = tmp.name
    
    mock_compress.return_value = compressed_path
    
    try:
        chunks = process_large_audio(small_audio_bytes, "test_small")
        
        assert len(chunks) == 1, "Small audio should produce single chunk"
        assert isinstance(chunks[0], AudioChunk)
        assert chunks[0].chunk_index == 0
        assert chunks[0].start_time == 0.0
        assert chunks[0].duration > 0
        
        mock_compress.assert_called_once()
    finally:
        if os.path.exists(compressed_path):
            os.remove(compressed_path)


@patch('app.services.media_processor.get_audio_info')
@patch('app.services.media_processor.compress_audio')
@patch('app.services.media_processor.chunk_audio')
def test_large_audio_multiple_chunks(mock_chunk, mock_compress, mock_get_info, large_audio_bytes, mock_audio_info):
    """Test that large audio files are chunked appropriately."""
    mock_audio_info['format']['duration'] = '600.0'
    mock_audio_info['format']['size'] = str(len(large_audio_bytes))
    mock_get_info.return_value = mock_audio_info
    
    with tempfile.NamedTemporaryFile(suffix='.flac', delete=False) as tmp:
        tmp.write(b"compressed audio")
        compressed_path = tmp.name
    
    mock_compress.return_value = compressed_path
    
    mock_chunk_paths = []
    for i in range(3):
        tmp = tempfile.NamedTemporaryFile(suffix=f'_chunk_{i}.flac', delete=False)
        tmp.write(b"chunk audio")
        tmp.close()
        mock_chunk_paths.append(tmp.name)
    
    mock_chunk.return_value = mock_chunk_paths
    
    try:
        chunks = process_large_audio(large_audio_bytes, "test_large")
        
        assert len(chunks) >= 1, "Large audio should produce at least one chunk"
        
        for idx, chunk in enumerate(chunks):
            assert isinstance(chunk, AudioChunk)
            assert chunk.chunk_index == idx
            
            if idx > 0:
                assert chunk.start_time > chunks[idx-1].start_time, "Chunks should have increasing start times"
    finally:
        if os.path.exists(compressed_path):
            os.remove(compressed_path)
        for path in mock_chunk_paths:
            if os.path.exists(path):
                os.remove(path)


@patch('app.services.media_processor.get_audio_info')
@patch('app.services.media_processor.compress_audio')
def test_audio_chunk_metadata(mock_compress, mock_get_info, small_audio_bytes, mock_audio_info):
    """Test that AudioChunk objects contain correct metadata."""
    mock_get_info.return_value = mock_audio_info
    
    with tempfile.NamedTemporaryFile(suffix='.flac', delete=False) as tmp:
        tmp.write(b"compressed audio")
        compressed_path = tmp.name
    
    mock_compress.return_value = compressed_path
    
    try:
        chunks = process_large_audio(small_audio_bytes, "test_metadata")
        
        assert len(chunks) > 0
        chunk = chunks[0]
        
        assert hasattr(chunk, 'file_path')
        assert hasattr(chunk, 'chunk_index')
        assert hasattr(chunk, 'start_time')
        assert hasattr(chunk, 'duration')
        
        assert isinstance(chunk.file_path, str)
        assert isinstance(chunk.chunk_index, int)
        assert isinstance(chunk.start_time, float)
        assert isinstance(chunk.duration, float)
        
        assert chunk.duration > 0, "Chunk duration should be positive"
    finally:
        if os.path.exists(compressed_path):
            os.remove(compressed_path)


def test_audio_chunk_dataclass():
    """Test AudioChunk dataclass creation."""
    chunk = AudioChunk(
        file_path="/tmp/test.flac",
        chunk_index=0,
        start_time=0.0,
        duration=240.0
    )
    
    assert chunk.file_path == "/tmp/test.flac"
    assert chunk.chunk_index == 0
    assert chunk.start_time == 0.0
    assert chunk.duration == 240.0


@patch('app.services.media_processor.get_audio_info')
def test_get_audio_info_timeout_handling(mock_get_info):
    """Test that audio info retrieval handles timeouts gracefully."""
    import subprocess
    mock_get_info.side_effect = subprocess.TimeoutExpired(cmd=['ffprobe'], timeout=30)
    
    with pytest.raises(subprocess.TimeoutExpired):
        get_audio_info("/tmp/test.wav")
