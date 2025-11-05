from dash import html

def render_audio_player(audio_id: str):
    return html.Div([
        html.Audio(
            id="audio-player",
            src=f"/audio/{audio_id}",
            controls=True,
            style={
                'width': '100%',
                'borderRadius': '8px',
                'outline': 'none'
            }
        )
    ], style={
        'marginBottom': '20px',
        'padding': '10px',
        'backgroundColor': '#ffffff',
        'borderRadius': '8px',
        'border': '1px solid #e5e7eb'
    })
