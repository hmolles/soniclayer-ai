import dash_player
from dash import html

def render_audio_player(audio_id: str):
    return html.Div([
        dash_player.DashPlayer(
            id="audio-player",
            url=f"/audio/{audio_id}",
            controls=True,
            playing=False,
            volume=0.8,
            muted=False,
            loop=False,
            playbackRate=1,
            intervalCurrentTime=250,
            width="100%",
            height="50px",
            style={
                'borderRadius': '8px',
                'overflow': 'hidden',
                'backgroundColor': '#ffffff',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
            }
        )
    ], style={
        'marginBottom': '20px',
        'padding': '10px',
        'backgroundColor': '#ffffff',
        'borderRadius': '8px',
        'border': '1px solid #e5e7eb'
    })
