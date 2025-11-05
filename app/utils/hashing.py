import hashlib

def generate_audio_hash(audio_bytes: bytes) -> str:
    """Generate a SHA256 hash from audio bytes to use as a unique ID."""
    return hashlib.sha256(audio_bytes).hexdigest()