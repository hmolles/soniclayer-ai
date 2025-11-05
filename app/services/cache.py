import redis

redis_conn = redis.Redis(host="localhost", port=6379, db=0)

def get_cached_transcript(key: str) -> str | None:
    result = redis_conn.get(key)
    return result.decode("utf-8") if result else None

def set_cached_transcript(key: str, transcript: str, ttl: int = 86400):
    redis_conn.setex(key, ttl, transcript)

def update_audio_status(audio_id: str, status: str):
    redis_conn.set(f"status:{audio_id}", status, ex=3600)

def get_audio_status(audio_id: str) -> str | None:
    status = redis_conn.get(f"status:{audio_id}")
    return status.decode("utf-8") if status else None