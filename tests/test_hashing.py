from app.utils.hashing import generate_audio_hash


def test_generate_audio_hash_consistency():
    """Test hash generation is deterministic."""
    data = b"sample audio content"
    hash1 = generate_audio_hash(data)
    hash2 = generate_audio_hash(data)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_different_content_different_hash():
    """Test different content produces different hashes."""
    bytes1 = b"First audio file"
    bytes2 = b"Second audio file"
    hash1 = generate_audio_hash(bytes1)
    hash2 = generate_audio_hash(bytes2)
    
    assert hash1 != hash2


def test_hash_format():
    """Test hash is valid hex string of expected length."""
    test_bytes = b"Test audio data"
    hash_result = generate_audio_hash(test_bytes)
    
    assert isinstance(hash_result, str)
    assert len(hash_result) == 64  # SHA256 produces 64 hex characters
    assert all(c in '0123456789abcdef' for c in hash_result)


def test_empty_bytes_hash():
    """Test hashing empty bytes works correctly."""
    empty_bytes = b""
    hash_result = generate_audio_hash(empty_bytes)
    
    assert isinstance(hash_result, str)
    assert len(hash_result) == 64
