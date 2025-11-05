from dashboard.components.metadata_panel import render_metadata_panel


def test_render_metadata_panel():
    """Test metadata panel with full segment data."""
    segment = {
        "topic": "Food",
        "tone": "Informative",
        "transcript": "Oat milk discussion",
        "persona_scores": {"genz": 5, "parents": 4},
        "note": "Repeated theme"
    }
    panel = render_metadata_panel(segment)
    assert panel is not None


def test_render_metadata_missing_persona():
    """Test graceful handling of missing persona scores."""
    segment = {
        "topic": "Test",
        "tone": "Neutral",
        "transcript": "Test segment"
        # No persona_scores
    }
    
    result = render_metadata_panel(segment)
    assert result is not None


def test_render_metadata_no_segment():
    """Test display when no active segment (None passed)."""
    result = render_metadata_panel(None)
    assert result is not None


def test_render_metadata_partial_data():
    """Test with minimal segment data."""
    segment = {
        "transcript": "Minimal segment"
    }
    
    result = render_metadata_panel(segment)
    assert result is not None


def test_render_metadata_empty_transcript():
    """Test handling of empty transcript."""
    segment = {
        "transcript": "",
        "topic": "Unknown",
        "tone": "Neutral"
    }
    
    result = render_metadata_panel(segment)
    assert result is not None


def test_render_metadata_with_complex_scores():
    """Test with nested persona score objects."""
    segment = {
        "topic": "Technology",
        "tone": "Excited",
        "transcript": "New tech announcement",
        "persona_scores": {
            "genz": {"score": 4, "opinion": "Cool!"},
            "advertiser": {"score": 5, "opinion": "Great commercial value"}
        }
    }
    
    result = render_metadata_panel(segment)
    assert result is not None
