from app.services.classifier import classify_segment, classify_transcript_segments

def test_classify_segment():
    text = "Today we're discussing oat milk and its health benefits."
    result = classify_segment(text)
    assert "topic" in result
    assert "tone" in result

def test_classify_transcript_segments():
    segments = [{"text": "Talking about oat milk..."}, {"text": "Reality TV finale..."}]
    results = classify_transcript_segments(segments)
    assert len(results) == 2
    assert all("topic" in r and "tone" in r for r in results)