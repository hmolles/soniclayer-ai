import requests

def fetch_segments(audio_id: str, api_base: str = "http://localhost:8000") -> list:
    response = requests.get(f"{api_base}/segments/{audio_id}")
    response.raise_for_status()
    return response.json()["segments"]