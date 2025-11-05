import plotly.graph_objects as go
from dash import dcc

def render_waveform_with_highlight(time, amplitude, segments, cursor_position=None):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=time,
        y=amplitude,
        mode='lines',
        name='Waveform',
        line=dict(color='lightblue')
    ))

    for seg in segments:
        is_active = cursor_position and seg["start"] <= cursor_position <= seg["end"]
        fill = "rgba(255, 0, 0, 0.4)" if is_active else "rgba(255, 0, 0, 0.2)"

        fig.add_shape(
            type="rect",
            x0=seg["start"],
            x1=seg["end"],
            y0=min(amplitude),
            y1=max(amplitude),
            fillcolor=fill,
            line=dict(width=0)
        )

    if cursor_position is not None:
        fig.add_shape(
            type="line",
            x0=cursor_position,
            x1=cursor_position,
            y0=min(amplitude),
            y1=max(amplitude),
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