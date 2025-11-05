import json
from fastapi.testclient import TestClient
from app.main import app
from app.services.cache import redis_conn

client = TestClient(app)

def test_get_enriched_segments():
    audio_id = "test123"
    redis_conn.set(f"transcript_segments:{audio_id}", json.dumps([
        {"start": 0.0, "end": 10.0, "text": "Welcome to the show."},
        {"start": 10.0, "end": 20.0, "text": "Talking about oat milk."}
    ]))
    redis_conn.set(f"classifier_output:{audio_id}", json.dumps([
        {"topic": "Intro", "tone": "Neutral"},
        {"topic": "Food", "tone": "Informative"}
    ]))
    redis_conn.set(f"persona_feedback:{audio_id}", json.dumps([
        {"genz": 4, "parents": 3},
        {"genz": 5, "parents": 4}
    ]))

    response = client.get(f"/segments/{audio_id}")
    assert response.status_code == 200
    segments = response.json()["segments"]
    assert len(segments) == 2
    assert "transcript" in segments[0]
    assert "topic" in segments[1]
    assert "persona_scores" in segments[1]

def test_get_segments_missing_data():
    response = client.get("/segments/missing_id")
    assert response.status_code == 404