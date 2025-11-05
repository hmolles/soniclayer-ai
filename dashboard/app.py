from dash import Dash, Input, Output, State, dcc, html, dash
import sys
from pathlib import Path
from components.waveform import render_waveform_with_highlight
from components.audio_player import render_audio_player
from components.metadata_panel import render_metadata_panel
from services.audio_utils import extract_waveform
from services.api_client import fetch_segments

# Get audio_id from command line or use default
audio_id = sys.argv[1] if len(sys.argv) > 1 else "ebeb643592f3ae3097bba2e0334414df2d8652f8f73f6ab74d1a61c79b544275"
audio_path = f"uploads/{audio_id}.wav"

# Check if file exists
if not Path(audio_path).exists():
    print(f"Error: Audio file not found: {audio_path}")
    print(f"Usage: python dashboard/app.py <audio_id>")
    sys.exit(1)

print(f"Loading dashboard for audio: {audio_id}")
time, amplitude = extract_waveform(audio_path)
segments = fetch_segments(audio_id)
print(f"Loaded {len(segments)} segments")

# Debug: Print first 3 segments to understand structure
if segments:
    print("\n=== First 3 Segments ===")
    for i, seg in enumerate(segments[:3]):
        print(f"Segment {i}: {seg['start']:.2f}s - {seg['end']:.2f}s")
        print(f"  Transcript: {seg.get('transcript', 'NO TRANSCRIPT')[:80]}")
        print(f"  Topic: {seg.get('topic', 'N/A')}, Tone: {seg.get('tone', 'N/A')}")
    print("========================\n")

app = Dash(__name__, assets_folder='assets')

# Add audio proxy endpoint to serve audio through port 5000
@app.server.route('/audio/<audio_id>')
def proxy_audio(audio_id):
    import requests
    from flask import Response, stream_with_context
    
    # Fetch audio from backend
    backend_url = f"http://localhost:8000/audio/{audio_id}"
    try:
        # Stream the audio from backend to browser
        r = requests.get(backend_url, stream=True)
        return Response(
            stream_with_context(r.iter_content(chunk_size=8192)),
            content_type='audio/wav',
            headers={
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'no-cache'
            }
        )
    except Exception as e:
        return Response(f"Error fetching audio: {str(e)}", status=500)

# Enhanced layout with better styling
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🎵 SonicLayer AI - Audio Analysis Dashboard", style={
            "margin": "0",
            "color": "#111827",
            "fontSize": "28px"
        }),
        html.P(f"Audio ID: {audio_id[:16]}...", style={
            "margin": "4px 0 0 0",
            "color": "#6b7280",
            "fontSize": "14px"
        })
    ], style={
        "padding": "20px",
        "backgroundColor": "#ffffff",
        "borderBottom": "2px solid #e5e7eb",
        "marginBottom": "20px"
    }),
    
    # Main content area - two columns
    html.Div([
        # Left column - Waveform and audio player
        html.Div([
            render_audio_player(audio_id),
            dcc.Graph(
                id="waveform-graph",
                figure=render_waveform_with_highlight(time, amplitude, segments),
                style={"height": "400px"}
            ),
        ], style={
            "flex": "1",
            "marginRight": "20px",
            "minWidth": "0"
        }),
        
        # Right column - Metadata panel
        html.Div(
            id="segment-metadata",
            style={
                "width": "450px",
                "backgroundColor": "#ffffff",
                "borderRadius": "8px",
                "border": "1px solid #e5e7eb",
                "maxHeight": "600px",
                "overflowY": "auto",
                "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
            }
        )
    ], style={
        "display": "flex",
        "padding": "0 20px",
        "marginBottom": "20px"
    }),
    
    # Hidden components for state management
    dcc.Interval(id="playback-sync", interval=1000, n_intervals=0),
    dcc.Store(id="user-clicked", data=False),
    dcc.Store(id='current-time-store', data=0),
    
], style={
    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    "backgroundColor": "#f3f4f6",
    "minHeight": "100vh"
})
# Clientside callback to update current time from audio player
app.clientside_callback(
    """
    function(n_intervals) {
        const audioElement = document.getElementById('audio-player');
        
        if (audioElement && audioElement.currentTime !== undefined) {
            return audioElement.currentTime;
        }
        
        return 0;
    }
    """,
    Output('current-time-store', 'data'),
    Input('playback-sync', 'n_intervals')
)


# Clientside callback to seek audio when waveform is clicked
app.clientside_callback(
    """
    function(click_data) {
        if (!click_data) {
            return window.dash_clientside.no_update;
        }
        
        // Get clicked time from waveform
        const clicked_time = click_data.points[0].x;
        
        // Find and seek the audio element
        const audioElement = document.getElementById('audio-player');
        if (audioElement) {
            audioElement.currentTime = clicked_time;
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('audio-player', 'id'),  # Dummy output (we just need to trigger on click)
    Input('waveform-graph', 'clickData')
)

# Global state to track current segment
_current_segment_index = -1
# Callback 1: Auto-update waveform and metadata during playback
@app.callback(
    Output("waveform-graph", "figure"),
    Output("segment-metadata", "children", allow_duplicate=True),
    Output("user-clicked", "data", allow_duplicate=True),
    Input('current-time-store', 'data'),
    State("user-clicked", "data"),
    prevent_initial_call=True
)
def auto_update_playback(current_time, user_clicked):
    global _current_segment_index
    
    # If user just clicked, reset flag and return
    if user_clicked:
        return dash.no_update, dash.no_update, False
    
    # Skip if no valid time
    if current_time is None or current_time < 0:
        return dash.no_update, dash.no_update, False
    
    # Find active segment
    active_segment = None
    active_index = -1
    for i, seg in enumerate(segments):
        if seg["start"] <= current_time <= seg["end"]:
            active_segment = seg
            active_index = i
            break
    
    # No matching segment
    if not active_segment:
        return dash.no_update, dash.no_update, False
    
    # Only update metadata if we crossed into a new segment
    if active_index != _current_segment_index:
        _current_segment_index = active_index
        # Update waveform cursor and metadata
        fig = render_waveform_with_highlight(time, amplitude, segments, cursor_position=current_time)
        metadata = render_metadata_panel(active_segment)
        return fig, metadata, False
    else:
        # Same segment - just update cursor, no metadata change
        fig = render_waveform_with_highlight(time, amplitude, segments, cursor_position=current_time)
        return fig, dash.no_update, False

# Callback 2: Handle waveform clicks for seeking
@app.callback(
    Output("segment-metadata", "children"),
    Output("user-clicked", "data"),
    Input("waveform-graph", "clickData"),
    prevent_initial_call=True
)
def handle_waveform_click(click_data):
    if click_data is None:
        return dash.no_update, dash.no_update
    
    # Get clicked time from waveform
    clicked_time = click_data['points'][0]['x']
    
    # Find the segment containing this time
    active_segment = next(
        (seg for seg in segments if seg["start"] <= clicked_time <= seg["end"]),
        None
    )
    
    # Update metadata
    metadata = render_metadata_panel(active_segment) if active_segment else "No segment at this time position."
    
    # Seek player to clicked time and set user-clicked flag
    return metadata, True

# Callback 3: Initialize metadata panel on first load
@app.callback(
    Output("segment-metadata", "children", allow_duplicate=True),
    Input("waveform-graph", "id"),
    prevent_initial_call='initial_duplicate'
)
def initialize_metadata(_):
    return render_metadata_panel(segments[0]) if segments else "No segments available."

if __name__ == "__main__":
    print(f"\n🚀 Starting dashboard server...")
    print(f"📊 Open in browser: http://localhost:8050")
    print(f"🎵 Audio: {audio_id}")
    print(f"📈 Segments loaded: {len(segments)}")
    print(f"\nPress Ctrl+C to stop\n")
    import os
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
