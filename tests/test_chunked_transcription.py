import pytest
from unittest.mock import patch, MagicMock
from app.services.transcryption import transcribe_chunked_audio, transcribe_audio_with_timestamps
from app.services.media_processor import AudioChunk
import time


@pytest.fixture
def mock_single_chunk():
    """Create a mock single chunk for testing."""
    chunk = AudioChunk(
        file_path="/tmp/test_chunk_0.flac",
        chunk_index=0,
        start_time=0.0,
        duration=10.0
    )
    return [chunk]


@pytest.fixture
def mock_multiple_chunks():
    """Create mock multiple chunks for testing."""
    chunks = [
        AudioChunk(file_path="/tmp/test_chunk_0.flac", chunk_index=0, start_time=0.0, duration=240.0),
        AudioChunk(file_path="/tmp/test_chunk_1.flac", chunk_index=1, start_time=240.0, duration=240.0),
        AudioChunk(file_path="/tmp/test_chunk_2.flac", chunk_index=2, start_time=480.0, duration=120.0),
    ]
    return chunks


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
def test_single_chunk_transcription(mock_transcribe, mock_single_chunk):
    """Test transcription with a single chunk (no rate limiting needed)."""
    mock_transcribe.return_value = [
        {"start": 0.0, "end": 5.0, "text": "First segment"},
        {"start": 5.0, "end": 10.0, "text": "Second segment"}
    ]
    
    result = transcribe_chunked_audio(mock_single_chunk)
    
    assert len(result) == 2
    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 5.0
    assert result[0]["text"] == "First segment"
    assert mock_transcribe.call_count == 1


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
def test_multiple_chunks_transcription(mock_transcribe, mock_multiple_chunks):
    """Test transcription with multiple chunks (requires rate limiting and timestamp stitching)."""
    mock_transcribe.side_effect = [
        [
            {"start": 0.0, "end": 10.0, "text": "Chunk 0 segment 1"},
            {"start": 10.0, "end": 20.0, "text": "Chunk 0 segment 2"}
        ],
        [
            {"start": 0.0, "end": 15.0, "text": "Chunk 1 segment 1"},
            {"start": 15.0, "end": 30.0, "text": "Chunk 1 segment 2"}
        ],
        [
            {"start": 0.0, "end": 10.0, "text": "Chunk 2 segment 1"}
        ]
    ]
    
    start_time = time.time()
    result = transcribe_chunked_audio(mock_multiple_chunks)
    elapsed_time = time.time() - start_time
    
    assert len(result) == 5
    
    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 10.0
    assert result[0]["text"] == "Chunk 0 segment 1"
    
    assert result[2]["start"] == 240.0
    assert result[2]["end"] == 255.0
    assert result[2]["text"] == "Chunk 1 segment 1"
    
    assert result[4]["start"] == 480.0
    assert result[4]["end"] == 490.0
    assert result[4]["text"] == "Chunk 2 segment 1"
    
    assert mock_transcribe.call_count == 3
    
    assert elapsed_time >= 40, "Should have rate limiting delays between chunks (20s * 2 = 40s)"


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
def test_timestamp_stitching_accuracy(mock_transcribe, mock_multiple_chunks):
    """Test that timestamps are correctly adjusted across chunk boundaries."""
    mock_transcribe.side_effect = [
        [{"start": 0.0, "end": 30.0, "text": "First chunk content"}],
        [{"start": 0.0, "end": 30.0, "text": "Second chunk content"}],
        [{"start": 0.0, "end": 30.0, "text": "Third chunk content"}]
    ]
    
    result = transcribe_chunked_audio(mock_multiple_chunks)
    
    assert len(result) == 3
    
    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 30.0
    
    assert result[1]["start"] == 240.0
    assert result[1]["end"] == 270.0
    
    assert result[2]["start"] == 480.0
    assert result[2]["end"] == 510.0
    
    for i in range(1, len(result)):
        assert result[i]["start"] >= result[i-1]["end"], "Timestamps should be monotonically increasing"


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
def test_empty_chunk_handling(mock_transcribe):
    """Test handling of chunks that produce no segments."""
    chunks = [
        AudioChunk(file_path="/tmp/chunk_0.flac", chunk_index=0, start_time=0.0, duration=10.0),
        AudioChunk(file_path="/tmp/chunk_1.flac", chunk_index=1, start_time=10.0, duration=10.0)
    ]
    
    mock_transcribe.side_effect = [
        [{"start": 0.0, "end": 5.0, "text": "Content"}],
        []
    ]
    
    result = transcribe_chunked_audio(chunks)
    
    assert len(result) == 1
    assert result[0]["text"] == "Content"


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
def test_rate_limiting_between_chunks(mock_transcribe, mock_multiple_chunks):
    """Test that rate limiting is applied between chunk transcriptions."""
    mock_transcribe.return_value = [{"start": 0.0, "end": 10.0, "text": "Test"}]
    
    start_time = time.time()
    result = transcribe_chunked_audio(mock_multiple_chunks)
    elapsed_time = time.time() - start_time
    
    expected_min_delay = 20 * (len(mock_multiple_chunks) - 1)
    assert elapsed_time >= expected_min_delay, f"Should wait at least {expected_min_delay}s for rate limiting"
    
    assert mock_transcribe.call_count == len(mock_multiple_chunks)


@patch('builtins.open', side_effect=FileNotFoundError("Chunk file not found"))
def test_missing_chunk_file_error(mock_open, mock_single_chunk):
    """Test error handling when chunk file is missing."""
    with pytest.raises(FileNotFoundError):
        transcribe_chunked_audio(mock_single_chunk)


@patch('app.services.transcryption.transcribe_audio_with_timestamps')
def test_transcription_error_propagation(mock_transcribe, mock_single_chunk):
    """Test that transcription errors are properly propagated."""
    mock_transcribe.side_effect = Exception("Azure API error")
    
    with pytest.raises(Exception) as exc_info:
        transcribe_chunked_audio(mock_single_chunk)
    
    assert "Azure API error" in str(exc_info.value)
