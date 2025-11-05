import requests

def fetch_segments(audio_id: str, api_base: str = "http://localhost:8000") -> list:
    """
    Fetch segments for an audio ID from the backend API.
    
    Returns:
        List of segments, or empty list if not found or error occurs.
    """
    try:
        response = requests.get(f"{api_base}/segments/{audio_id}")
        response.raise_for_status()
        return response.json()["segments"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Warning: No segments found for audio ID {audio_id}")
            return []
        else:
            print(f"Error fetching segments: {e}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to backend API: {e}")
        return []
    except (KeyError, ValueError) as e:
        print(f"Error parsing segments response: {e}")
        return []
