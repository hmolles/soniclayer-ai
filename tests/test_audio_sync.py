import pytest


def test_active_segment_match():
    """Test finding active segment based on current playback time."""
    segments = [
        {"start": 0.0, "end": 10.0, "topic": "Intro", "tone": "Neutral", "transcript": "Welcome"},
        {"start": 10.0, "end": 20.0, "topic": "Food", "tone": "Informative", "transcript": "Oat milk"}
    ]
    current_time = 15.0
    active = next((s for s in segments if s["start"] <= current_time <= s["end"]), None)
    assert active["topic"] == "Food"


def test_segment_boundary_exact_match():
    """Test segment matching at exact time boundaries."""
    segments = [
        {"start": 0.0, "end": 10.0, "id": "seg1"},
        {"start": 10.0, "end": 20.0, "id": "seg2"}
    ]
    
    # At exact boundary (10.0)
    current_time = 10.0
    active = next((s for s in segments if s["start"] <= current_time <= s["end"]), None)
    assert active is not None


def test_no_active_segment():
    """Test when current time is outside all segments."""
    segments = [
        {"start": 0.0, "end": 10.0, "id": "seg1"},
        {"start": 10.0, "end": 20.0, "id": "seg2"}
    ]
    current_time = 25.0
    active = next((s for s in segments if s["start"] <= current_time <= s["end"]), None)
    assert active is None


def test_first_segment_match():
    """Test matching first segment."""
    segments = [
        {"start": 0.0, "end": 5.0, "id": "seg1"},
        {"start": 5.0, "end": 10.0, "id": "seg2"}
    ]
    current_time = 2.0
    active = next((s for s in segments if s["start"] <= current_time <= s["end"]), None)
    assert active["id"] == "seg1"


def test_last_segment_match():
    """Test matching last segment."""
    segments = [
        {"start": 0.0, "end": 5.0, "id": "seg1"},
        {"start": 5.0, "end": 10.0, "id": "seg2"}
    ]
    current_time = 8.0
    active = next((s for s in segments if s["start"] <= current_time <= s["end"]), None)
    assert active["id"] == "seg2"


def test_empty_segments_list():
    """Test behavior with no segments."""
    segments = []
    current_time = 5.0
    active = next((s for s in segments if s["start"] <= current_time <= s["end"]), None)
    assert active is None


@pytest.mark.skip(reason="Requires Dash testing framework with Selenium")
def test_dashboard_callback_integration():
    """
    Full integration test for dashboard callbacks.
    Requires dash.testing framework.
    """
    pass
