import plotly.graph_objects as go
from dash import dcc

def render_waveform_with_highlight(time, amplitude, segments, cursor_position=None, amp_min=None, amp_max=None, audio_id=None):
    """
    Render waveform with segment highlights and optional cursor.
    
    Args:
        time: Array of time values
        amplitude: Array of amplitude values
        segments: List of segment dicts with start/end times
        cursor_position: Current playback position (optional)
        amp_min: Cached minimum amplitude (optional, for performance)
        amp_max: Cached maximum amplitude (optional, for performance)
        audio_id: Audio file ID to display as title (optional)
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=time,
        y=amplitude,
        mode='lines',
        name='Waveform',
        line=dict(color='#0f172a')  # slate-900 dark color
    ))

    # Use cached min/max if provided, otherwise calculate
    y_min = amp_min if amp_min is not None else min(amplitude)
    y_max = amp_max if amp_max is not None else max(amplitude)

    for seg in segments:
        is_active = cursor_position and seg["start"] <= cursor_position <= seg["end"]
        fill = "rgba(200, 200, 255, 0.4)" if is_active else "rgba(255, 255, 255, 0.0)"  # Light blue for active, transparent white for inactive

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

    # Set title - use audio_id if provided, otherwise default text
    title_text = audio_id if audio_id else "Audio Waveform with Segment Highlight"
    
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(
                size=13,
                color="#94a3b8"  # slate-400, matching header style
            ),
            x=0,  # Left-align
            xanchor='left'
        ),
        xaxis=dict(
            title="",  # Remove x-axis title
            showticklabels=False  # Hide x-axis tick labels
        ),
        yaxis=dict(
            title="",  # Remove y-axis title
            showticklabels=False  # Hide y-axis tick labels
        ),
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    return fig