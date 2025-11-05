import pytest
from unittest.mock import patch, MagicMock
from app.services.media_processor import AudioChunk
from app.services.transcryption import transcribe_chunked_audio
import tempfile
import os


@pytest.fixture
def single_chunk_with_real_files():
    """Create a single chunk with a real temporary file."""
    with tempfile.NamedTemporaryFile(suffix='.flac', delete=False) as tmp:
        tmp.write(b"test audio data single chunk")
        tmp_path = tmp.name
    
    chunk = AudioChunk(
        file_path=tmp_path,
        chunk_index=0,
        start_time=0.0,
        duration=60.0
    )
    
    yield [chunk]
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


@pytest.fixture
def multiple_chunks_with_real_files():
    """Create multiple chunks with real temporary files."""
    chunks = []
    temp_files = []
    
    for i in range(3):
        with tempfile.NamedTemporaryFile(suffix=f'_chunk_{i}.flac', delete=False) as tmp:
            tmp.write(f"test audio data chunk {i}".encode())
            temp_files.append(tmp.name)
        
        chunk = AudioChunk(
            file_path=temp_files[i],
            chunk_index=i,
            start_time=i * 240.0,
            duration=240.0
        )
        chunks.append(chunk)
    
    yield chunks
    
    for path in temp_files:
        if os.path.exists(path):
            os.remove(path)


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
def test_single_chunk_no_stitching(mock_transcribe, single_chunk_with_real_files):
    """Test that single chunk transcription works without timestamp stitching."""
    mock_transcribe.return_value = [
        {"start": 0.0, "end": 10.0, "text": "First segment"},
        {"start": 10.0, "end": 20.0, "text": "Second segment"}
    ]
    
    result = transcribe_chunked_audio(single_chunk_with_real_files)
    
    assert len(result) == 2
    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 10.0
    assert result[0]["text"] == "First segment"
    assert result[1]["start"] == 10.0
    assert result[1]["end"] == 20.0


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
@patch('app.services.transcryption.time.sleep')
def test_multiple_chunks_with_stitching(mock_sleep, mock_transcribe, multiple_chunks_with_real_files):
    """Test that multiple chunks are stitched correctly with timestamp offsets."""
    mock_transcribe.side_effect = [
        [
            {"start": 0.0, "end": 15.0, "text": "Chunk 0 first"},
            {"start": 15.0, "end": 30.0, "text": "Chunk 0 second"}
        ],
        [
            {"start": 0.0, "end": 20.0, "text": "Chunk 1 first"}
        ],
        [
            {"start": 0.0, "end": 10.0, "text": "Chunk 2 first"}
        ]
    ]
    
    result = transcribe_chunked_audio(multiple_chunks_with_real_files)
    
    assert len(result) == 4
    
    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 15.0
    assert result[0]["text"] == "Chunk 0 first"
    
    assert result[2]["start"] == 240.0
    assert result[2]["end"] == 260.0
    assert result[2]["text"] == "Chunk 1 first"
    
    assert result[3]["start"] == 480.0
    assert result[3]["end"] == 490.0
    assert result[3]["text"] == "Chunk 2 first"
    
    assert mock_sleep.call_count == 2


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
@patch('app.services.transcryption.time.sleep')
def test_rate_limiting_applied(mock_sleep, mock_transcribe, multiple_chunks_with_real_files):
    """Test that rate limiting delay is applied between chunks."""
    mock_transcribe.return_value = [{"start": 0.0, "end": 10.0, "text": "Test"}]
    
    transcribe_chunked_audio(multiple_chunks_with_real_files)
    
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0][0][0] == 20
    assert mock_sleep.call_args_list[1][0][0] == 20


def test_audio_chunk_creation():
    """Test AudioChunk object creation and attributes."""
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


def test_audio_chunk_ordering():
    """Test that AudioChunk maintains correct ordering."""
    chunks = [
        AudioChunk("/tmp/chunk0.flac", 0, 0.0, 240.0),
        AudioChunk("/tmp/chunk1.flac", 1, 240.0, 240.0),
        AudioChunk("/tmp/chunk2.flac", 2, 480.0, 120.0)
    ]
    
    for i in range(1, len(chunks)):
        assert chunks[i].chunk_index > chunks[i-1].chunk_index
        assert chunks[i].start_time > chunks[i-1].start_time


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
def test_empty_segments_handling(mock_transcribe, single_chunk_with_real_files):
    """Test handling when a chunk produces no segments."""
    mock_transcribe.return_value = []
    
    result = transcribe_chunked_audio(single_chunk_with_real_files)
    
    assert len(result) == 0
    assert isinstance(result, list)
