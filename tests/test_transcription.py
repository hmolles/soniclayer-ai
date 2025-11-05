from unittest.mock import patch, MagicMock
from app.services.transcryption import transcribe_audio
import tempfile
import os


@patch('app.services.transcryption.model')
def test_transcribe_audio_success(mock_model):
    """Test successful transcription with mocked Whisper model."""
    # Mock the transcribe method to return expected structure
    mock_model.transcribe.return_value = {
        "text": "This is a test transcription."
    }
    
    test_audio_bytes = b"fake wav data"
    result = transcribe_audio(test_audio_bytes)
    
    assert result == "This is a test transcription."
    assert mock_model.transcribe.called


@patch('app.services.transcryption.model')
def test_transcribe_audio_strips_whitespace(mock_model):
    """Test that transcription strips leading/trailing whitespace."""
    mock_model.transcribe.return_value = {
        "text": "   Text with spaces   "
    }
    
    test_audio_bytes = b"fake wav data"
    result = transcribe_audio(test_audio_bytes)
    
    assert result == "Text with spaces"


@patch('app.services.transcryption.model')
def test_transcribe_audio_cleanup(mock_model):
    """Verify temporary files are deleted after transcription."""
    mock_model.transcribe.return_value = {
        "text": "Test"
    }
    
    # Track if temp file is created and deleted
    created_files = []
    original_tempfile = tempfile.NamedTemporaryFile
    
    def tracking_tempfile(*args, **kwargs):
        temp = original_tempfile(*args, **kwargs)
        created_files.append(temp.name)
        return temp
    
    with patch('tempfile.NamedTemporaryFile', side_effect=tracking_tempfile):
        test_audio_bytes = b"fake wav data"
        transcribe_audio(test_audio_bytes)
    
    # Verify temp file was deleted
    if created_files:
        assert not os.path.exists(created_files[0])


@patch('app.services.transcryption.model')
def test_transcribe_audio_empty_result(mock_model):
    """Test handling of empty transcription result."""
    mock_model.transcribe.return_value = {
        "text": ""
    }
    
    test_audio_bytes = b"silent audio"
    result = transcribe_audio(test_audio_bytes)
    
    assert result == ""


@patch('app.services.transcryption.model')
def test_transcribe_audio_special_characters(mock_model):
    """Test transcription preserves special characters."""
    mock_model.transcribe.return_value = {
        "text": "Hello! How are you? I'm fine."
    }
    
    test_audio_bytes = b"fake wav data"
    result = transcribe_audio(test_audio_bytes)
    
    assert result == "Hello! How are you? I'm fine."
