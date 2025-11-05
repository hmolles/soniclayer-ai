from dash import html

def render_audio_player(audio_id: str):
    return html.Div([
        html.Audio(
            id="audio-player",
            src=f"/audio/{audio_id}",
            controls=True,
            style={
                'width': '100%',
                'outline': 'none'
            }
        )
    ], style={
        'marginBottom': '20px',
        'marginTop': '10px'
    })
