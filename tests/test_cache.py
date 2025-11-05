from app.services.cache import get_cached_transcript, set_cached_transcript

def test_cache_transcript():
    key = "test_audio_hash"
    value = "This is a test transcript."
    set_cached_transcript(key, value, ttl=60)
    cached = get_cached_transcript(key)
    assert cached == value