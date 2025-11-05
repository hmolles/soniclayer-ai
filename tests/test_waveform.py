from dashboard.services.audio_utils import extract_waveform
from dashboard.components.waveform import render_waveform_with_highlight
import numpy as np
from unittest.mock import patch
import os


def test_extract_waveform():
    """Test waveform extraction from audio file (requires real file)."""
    test_file = "uploads/sample.wav"
    if os.path.exists(test_file):
        time, amplitude = extract_waveform(test_file)
        assert len(time) == len(amplitude)
        assert len(time) > 100


def test_render_waveform_basic():
    """Test waveform renders with basic time/amplitude data."""
    time = np.linspace(0, 10, 1000)
    amplitude = np.sin(2 * np.pi * time)
    segments = []
    
    fig = render_waveform_with_highlight(time, amplitude, segments)
    
    assert fig is not None
    assert hasattr(fig, 'data')  # Plotly figure has data attribute


def test_render_waveform_with_segments():
    """Test segment highlighting overlay."""
    time = np.linspace(0, 10, 1000)
    amplitude = np.sin(2 * np.pi * time)
    segments = [
        {"start": 2.0, "end": 4.0, "topic": "Test"},
        {"start": 6.0, "end": 8.0, "topic": "Test2"}
    ]
    
    fig = render_waveform_with_highlight(time, amplitude, segments)
    
    assert fig is not None


def test_render_waveform_with_cursor():
    """Test playback cursor position."""
    time = np.linspace(0, 10, 1000)
    amplitude = np.sin(2 * np.pi * time)
    segments = []
    cursor_position = 5.0
    
    fig = render_waveform_with_highlight(time, amplitude, segments, cursor_position=cursor_position)
    
    assert fig is not None


def test_render_empty_segments():
    """Test rendering with no segments."""
    time = np.linspace(0, 5, 500)
    amplitude = np.random.randn(500)
    segments = []
    
    fig = render_waveform_with_highlight(time, amplitude, segments)
    assert fig is not None
