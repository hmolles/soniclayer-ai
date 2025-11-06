import plotly.graph_objects as go
from dash import dcc

def render_waveform_with_highlight(time, amplitude, segments, cursor_position=None, amp_min=None, amp_max=None):
    """
    Render waveform with segment highlights and optional cursor.
    
    Args:
        time: Array of time values
        amplitude: Array of amplitude values
        segments: List of segment dicts with start/end times
        cursor_position: Current playback position (optional)
        amp_min: Cached minimum amplitude (optional, for performance)
        amp_max: Cached maximum amplitude (optional, for performance)
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=time,
        y=amplitude,
        mode='lines',
        name='Waveform',
        line=dict(color='lightblue')
    ))

    # Use cached min/max if provided, otherwise calculate
    y_min = amp_min if amp_min is not None else min(amplitude)
    y_max = amp_max if amp_max is not None else max(amplitude)

    for seg in segments:
        is_active = cursor_position and seg["start"] <= cursor_position <= seg["end"]
        fill = "rgba(255, 0, 0, 0.4)" if is_active else "rgba(255, 0, 0, 0.2)"

        fig.add_shape(
            type="rect",
            x0=seg["start"],
            x1=seg["end"],
            y0=y_min,
            y1=y_max,
            fillcolor=fill,
            line=dict(width=0)
        )

    if cursor_position is not None:
        fig.add_shape(
            type="line",
            x0=cursor_position,
            x1=cursor_position,
            y0=y_min,
            y1=y_max,
            line=dict(color="blue", width=2, dash="dot")
        )

    fig.update_layout(
        title="Audio Waveform with Segment Highlight",
        xaxis_title="Time (s)",
        yaxis_title="Amplitude",
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    return fig