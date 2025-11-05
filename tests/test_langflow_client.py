import pytest
import httpx
import requests
from unittest.mock import patch, MagicMock
from app.services import langflow_client

# Sample segment payload
sample_segment = {
    "transcript": "This is a test segment about oat milk and its benefits.",
    "topic": "Food",
    "tone": "Informative",
    "tags": ["repetition"]
}

# Sample successful response from Langflow
mock_success_response = {
    "score": 4,
    "opinion": "Funny and relatable.",
    "rationale": "Rated 4 because the segment was humorous and matched Gen Z preferences.",
    "note": "Repeated theme",
    "confidence": 0.85
}

@patch("app.services.langflow_client.requests.post")
def test_call_langflow_chain_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_success_response
    mock_post.return_value = mock_response

    result = langflow_client.call_langflow_chain("genz", sample_segment)
    assert result["score"] == 4
    assert "opinion" in result
    assert "rationale" in result
    assert "confidence" in result
    assert isinstance(result["confidence"], float)

@patch("app.services.langflow_client.requests.post")
def test_call_langflow_chain_timeout(mock_post):
    mock_post.side_effect = requests.Timeout("Request timed out")
    with pytest.raises(TimeoutError) as excinfo:
        langflow_client.call_langflow_chain("genz", sample_segment)
    assert "timed out" in str(excinfo.value)

@patch("app.services.langflow_client.requests.post")
def test_call_langflow_chain_malformed_response(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "opinion": "Missing score field"
    }
    mock_post.return_value = mock_response

    with pytest.raises(ValueError) as excinfo:
        langflow_client.call_langflow_chain("genz", sample_segment)
    assert "Missing expected fields" in str(excinfo.value)

@patch("app.services.langflow_client.requests.post")
def test_call_langflow_chain_retry_logic(mock_post):
    # Simulate two failures followed by a success
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.json.return_value = mock_success_response

    mock_post.side_effect = [
        requests.Timeout("Connection timeout"),
        requests.RequestException("Connection error"),
        success_response
    ]

    result = langflow_client.call_langflow_chain("genz", sample_segment)
    assert result["score"] == 4
    assert result["confidence"] == 0.85

@patch("app.services.langflow_client.requests.post")
def test_call_langflow_chain_endpoint_routing(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_success_response
    mock_post.return_value = mock_response

    langflow_client.call_langflow_chain("genz", sample_segment)
    called_url = mock_post.call_args[0][0]
    assert "genz" in called_url