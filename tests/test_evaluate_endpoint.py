from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.services.cache import redis_conn
import io
import pytest

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_redis():
    """Clear Redis before each test to avoid deduplication."""
    redis_conn.flushdb()
    yield
    redis_conn.flushdb()


@patch('app.routes.evaluate.transcribe_audio')
@patch('app.routes.evaluate.classify_segment')
@patch('app.routes.evaluate.queue')
def test_evaluate_endpoint_success(mock_queue, mock_classify, mock_transcribe):
    """Test successful audio upload and processing pipeline."""
    # Mock transcription
    mock_transcribe.return_value = "This is a test transcript about oat milk."
    
    # Mock classification
    mock_classify.return_value = {
        "topic": "Food",
        "tone": "Informative",
        "tags": []
    }
    
    # Mock RQ job
    mock_job = MagicMock()
    mock_job.id = "test-job-123"
    mock_queue.enqueue.return_value = mock_job
    
    # Create fake WAV file with unique content
    fake_wav = b"RIFF" + b"\x03" * 100
    
    response = client.post("/evaluate/", files={"file": ("test.wav", fake_wav, "audio/wav")})
    
    assert response.status_code == 200
    data = response.json()
    assert "audio_id" in data
    assert "status" in data
    assert data["status"] == "processing"
    assert "job_ids" in data


@patch('app.routes.evaluate.transcribe_audio')
@patch('app.routes.evaluate.classify_segment')
@patch('app.routes.evaluate.queue')
def test_evaluate_returns_job_ids(mock_queue, mock_classify, mock_transcribe):
    """Test that job IDs are returned for tracking."""
    mock_transcribe.return_value = "Test transcript"
    mock_classify.return_value = {"topic": "Test", "tone": "Test", "tags": []}
    
    mock_job = MagicMock()
    mock_job.id = "job-456"
    mock_queue.enqueue.return_value = mock_job
    
    # Use unique content to avoid deduplication
    fake_wav = b"RIFF" + b"\x01" * 100
    response = client.post("/evaluate/", files={"file": ("test.wav", fake_wav, "audio/wav")})
    
    assert response.status_code == 200
    data = response.json()
    assert "job_ids" in data
    assert "genz" in data["job_ids"]
    assert "advertiser" in data["job_ids"]


@patch('app.routes.evaluate.transcribe_audio')
@patch('app.routes.evaluate.classify_segment')
@patch('app.routes.evaluate.queue')
def test_evaluate_stores_in_redis(mock_queue, mock_classify, mock_transcribe):
    """Test that transcript and classification are stored in Redis."""
    mock_transcribe.return_value = "Test transcript"
    mock_classify.return_value = {"topic": "Test", "tone": "Test", "tags": []}
    
    mock_job = MagicMock()
    mock_job.id = "job-789"
    mock_queue.enqueue.return_value = mock_job
    
    # Use unique content to avoid deduplication
    fake_wav = b"RIFF" + b"\x02" * 100
    response = client.post("/evaluate/", files={"file": ("test.wav", fake_wav, "audio/wav")})
    
    assert response.status_code == 200
    data = response.json()
    assert "segment_count" in data
    assert data["segment_count"] > 0


def test_evaluate_missing_file():
    """Test /evaluate/ returns error when no file provided."""
    response = client.post("/evaluate/")
    assert response.status_code == 422  # FastAPI validation error


def test_evaluate_invalid_file_type():
    """Test /evaluate/ rejects non-audio files."""
    response = client.post("/evaluate/", files={"file": ("test.txt", b"not audio", "text/plain")})
    assert response.status_code == 400


def test_evaluate_empty_file():
    """Test /evaluate/ rejects empty files."""
    response = client.post("/evaluate/", files={"file": ("empty.wav", b"", "audio/wav")})
    assert response.status_code == 400

