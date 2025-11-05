from dash import Dash, Input, Output, State, dcc, html, dash
import sys
import json
from pathlib import Path
from components.waveform import render_waveform_with_highlight
from components.audio_player import render_audio_player
from components.metadata_panel import render_metadata_panel
from components.navigation import render_navigation
from components.admin_page import render_admin_page
from components.file_browser import render_file_browser
from services.audio_utils import extract_waveform
from services.api_client import fetch_segments

# Get default audio_id from command line (for backwards compatibility)
default_audio_id = sys.argv[1] if len(sys.argv) > 1 else "50f5315356317fa1a803bc5a754e4899d3275b711590f5baa7db35947f04bf70"

print(f"Dashboard server starting...")
print(f"Default audio for command-line mode: {default_audio_id}")

# Initialize Dash app
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


def create_dashboard_layout():
    """Create the dashboard page structure (will be populated dynamically)"""
    return html.Div([
        # Header with navigation
        html.Div([
            html.Div([
                html.H1("🎵 SonicLayer AI - Audio Analysis Dashboard", style={
                    "margin": "0",
                    "color": "#111827",
                    "fontSize": "28px"
                }),
                html.P(id="dashboard-audio-id-display", children="Select an audio file from Files", style={
                    "margin": "4px 0 0 0",
                    "color": "#6b7280",
                    "fontSize": "14px"
                })
            ]),
            render_navigation("/dashboard")
        ], style={
            "padding": "20px",
            "backgroundColor": "#ffffff",
            "borderBottom": "2px solid #e5e7eb",
            "marginBottom": "20px",
            "position": "relative"
        }),
        
        # Main content area - two columns
        html.Div([
            # Left column - Waveform and audio player
            html.Div([
                html.Div(id="audio-player-container"),
                dcc.Graph(
                    id="waveform-graph",
                    figure={},
                    style={"height": "400px"},
                    config={'displayModeBar': False}
                ),
            ], style={
                "flex": "1",
                "marginRight": "20px",
                "minWidth": "0"
            }),
            
            # Right column - Metadata panel
            html.Div(
                id="segment-metadata",
                children=html.Div("Select an audio file to view analysis", style={"padding": "20px"}),
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
        dcc.Store(id='current-audio-id', data=None),
        dcc.Store(id='segments-store', data=[]),
        dcc.Store(id='waveform-data-store', data={'time': [], 'amplitude': []}),
    ], id="dashboard-page", style={"display": "none"})

# Main app layout with all pages
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    
    # File Browser Page
    html.Div(id="file-browser-page", children=render_file_browser(), style={"display": "none"}),
    
    # Dashboard Page
    create_dashboard_layout(),
    
    # Admin Page
    html.Div(id="admin-page", children=render_admin_page(), style={"display": "none"}),
    
], style={
    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    "backgroundColor": "#f3f4f6",
    "minHeight": "100vh"
})

# Routing callback - toggle page visibility
@app.callback(
    Output('file-browser-page', 'style'),
    Output('dashboard-page', 'style'),
    Output('admin-page', 'style'),
    Input('url', 'pathname'),
    Input('url', 'search')
)
def toggle_pages(pathname, search):
    """Show/hide pages based on pathname"""
    
    # Handle URL-encoded query strings in pathname (screenshot tool quirk)
    if '%3F' in pathname or '?' in pathname:
        if '?' in pathname:
            pathname, search = pathname.split('?', 1)
            search = '?' + search
        else:
            # URL-encoded case
            import urllib.parse
            pathname = urllib.parse.unquote(pathname)
            if '?' in pathname:
                pathname, search = pathname.split('?', 1)
                search = '?' + search
    
    # Default styles
    hidden = {"display": "none"}
    visible = {"display": "block"}
    
    if pathname == '/admin':
        return hidden, hidden, visible
    elif pathname == '/dashboard' or (pathname == '/' and search and 'audio_id=' in search):
        return hidden, visible, hidden
    elif pathname == '/files' or pathname == '/':
        return visible, hidden, hidden
    else:
        # Default to file browser
        return visible, hidden, hidden

# Load dashboard data when audio_id changes in URL (STORES ONLY)
@app.callback(
    Output('current-audio-id', 'data'),
    Output('segments-store', 'data'),
    Output('waveform-data-store', 'data'),
    Input('url', 'pathname'),
    Input('url', 'search')
)
def load_dashboard_data(pathname, search):
    """Load audio data when URL changes to dashboard with audio_id"""
    
    # Handle URL-encoded query strings
    if '%3F' in pathname or '?' in pathname:
        if '?' in pathname:
            pathname, search = pathname.split('?', 1)
            search = '?' + search
        else:
            import urllib.parse
            pathname = urllib.parse.unquote(pathname)
            if '?' in pathname:
                pathname, search = pathname.split('?', 1)
                search = '?' + search
    
    # Only load if we're on the dashboard page
    if pathname != '/dashboard' and not (pathname == '/' and search and 'audio_id=' in search):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Extract audio_id from URL
    audio_id = None
    if search:
        import urllib.parse
        params = urllib.parse.parse_qs(search.lstrip('?'))
        audio_id = params.get('audio_id', [None])[0]
    
    if not audio_id:
        # No audio selected
        return None, [], {'time': [], 'amplitude': []}
    
    # Load audio data
    audio_path = f"uploads/{audio_id}.wav"
    if not Path(audio_path).exists():
        return None, [], {'time': [], 'amplitude': []}
    
    print(f"Loading dashboard data for audio: {audio_id}")
    import numpy as np
    time, amplitude = extract_waveform(audio_path)
    segments = fetch_segments(audio_id)
    print(f"Loaded {len(segments)} segments")
    
    return audio_id, segments, {'time': time.tolist(), 'amplitude': amplitude.tolist()}

# Populate visual elements from stores
@app.callback(
    Output('audio-player-container', 'children'),
    Output('waveform-graph', 'figure'),
    Output('dashboard-audio-id-display', 'children'),
    Input('current-audio-id', 'data'),
    Input('segments-store', 'data'),
    Input('waveform-data-store', 'data'),
    prevent_initial_call=False
)
def populate_dashboard(audio_id, segments, waveform_data):
    import numpy as np
    
    print(f"[POPULATE] audio_id={audio_id}, segments={len(segments) if segments else 0}, waveform_has_data={bool(waveform_data and waveform_data.get('time'))}")
    
    if not audio_id or not segments or not waveform_data or not waveform_data.get('time'):
        print(f"[POPULATE] Returning empty - missing data")
        return html.Div("Select an audio file from Files"), {}, "Select an audio file from Files"
    
    # Create audio player
    player = render_audio_player(audio_id)
    
    # Create initial waveform
    time = np.array(waveform_data['time'])
    amplitude = np.array(waveform_data['amplitude'])
    fig = render_waveform_with_highlight(time, amplitude, segments)
    
    # Display text
    display_text = f"Audio ID: {audio_id[:16]}..."
    
    return player, fig, display_text

# Persona creation callback
@app.callback(
    Output('creation-feedback', 'children'),
    Output('persona-id-input', 'value'),
    Output('persona-name-input', 'value'),
    Output('persona-emoji-input', 'value'),
    Output('persona-description-input', 'value'),
    Output('persona-prompt-input', 'value'),
    Output('url', 'pathname'),
    Input('create-persona-button', 'n_clicks'),
    State('persona-id-input', 'value'),
    State('persona-name-input', 'value'),
    State('persona-emoji-input', 'value'),
    State('persona-description-input', 'value'),
    State('persona-prompt-input', 'value'),
    prevent_initial_call=True
)
def create_persona(n_clicks, persona_id, display_name, emoji, description, prompt_json):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Validate inputs
    if not persona_id or not display_name or not prompt_json:
        return html.Div("❌ Please fill in all required fields (*)", style={
            "color": "#dc2626",
            "padding": "12px",
            "backgroundColor": "#fee2e2",
            "borderRadius": "6px",
            "border": "1px solid #dc2626"
        }), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Validate persona_id format (lowercase, no spaces)
    if not persona_id.replace('_', '').isalnum() or persona_id != persona_id.lower():
        return html.Div("❌ Persona ID must be lowercase alphanumeric (underscores allowed)", style={
            "color": "#dc2626",
            "padding": "12px",
            "backgroundColor": "#fee2e2",
            "borderRadius": "6px",
            "border": "1px solid #dc2626"
        }), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Parse JSON (try to parse, but use as-is if it fails)
    try:
        parsed_prompt = json.loads(prompt_json)
    except:
        # If not valid JSON, create a simple structure
        parsed_prompt = {
            "system": prompt_json,
            "user_template": "Evaluate: {text}"
        }
    
    # Save persona to config files
    try:
        import os
        print(f"DEBUG: Creating persona {persona_id} with name {display_name}")
        
        # Add to backend config
        backend_config_path = Path("app/config/personas.py")
        dashboard_config_path = Path("dashboard/personas_config.py")
        langflow_config_path = Path("app/services/langflow_client.py")
        
        print(f"DEBUG: Backend config path: {backend_config_path.absolute()}")
        print(f"DEBUG: Path exists: {backend_config_path.exists()}")
        
        # Read backend config
        with open(backend_config_path, 'r') as f:
            backend_content = f.read()
        
        print(f"DEBUG: Read backend config, length: {len(backend_content)}")
        
        # Create new persona entry for backend
        new_backend_entry = f'''    {{
        "id": "{persona_id}",
        "display_name": "{display_name}",
        "emoji": "{emoji or '🎯'}",
        "worker_module": "app.workers.{persona_id}_worker",
        "chain_name": "{persona_id}_chain",
        "description": "{description or 'Custom persona'}"
    }}'''
        
        # Insert before closing bracket
        backend_content = backend_content.replace(
            "\n]",
            f",\n{new_backend_entry}\n]"
        )
        
        print(f"DEBUG: Updated backend config, new length: {len(backend_content)}")
        
        # Write backend config
        print(f"DEBUG: Writing backend config...")
        with open(backend_config_path, 'w') as f:
            f.write(backend_content)
        print(f"DEBUG: Backend config written successfully")
        
        # Update dashboard config
        with open(dashboard_config_path, 'r') as f:
            dashboard_content = f.read()
        
        new_dashboard_entry = f'''    {{
        "id": "{persona_id}",
        "display_name": "{display_name}",
        "emoji": "{emoji or '🎯'}",
        "description": "{description or 'Custom persona'}"
    }}'''
        
        dashboard_content = dashboard_content.replace(
            "\n]",
            f",\n{new_dashboard_entry}\n]"
        )
        
        with open(dashboard_config_path, 'w') as f:
            f.write(dashboard_content)
        
        # Update langflow prompts
        with open(langflow_config_path, 'r') as f:
            langflow_content = f.read()
        
        # Find PERSONA_PROMPTS dict and add new entry
        new_prompt_entry = f'''    "{persona_id}_chain": {json.dumps(parsed_prompt, indent=8).replace("        ", "    ")},
}}'''
        
        langflow_content = langflow_content.replace(
            "\n}",
            f"\n{new_prompt_entry}"
        )
        
        with open(langflow_config_path, 'w') as f:
            f.write(langflow_content)
        
        print(f"DEBUG: Creating worker file...")
        
        # Create worker file
        worker_template = f'''import json
import logging
from app.services.cache import redis_conn
from app.services.langflow_client import call_langflow_chain

logger = logging.getLogger(__name__)


def process_transcript(audio_id, transcript_segments, classifier_results):
    """
    Process transcript segments using {display_name} Langflow chain.
    
    Args:
        audio_id: Unique audio identifier (hash of audio file)
        transcript_segments: List of segment dicts with 'text' field
        classifier_results: List of classification dicts with 'topic' and 'tone'
    """
    feedback = []
    
    for i, segment in enumerate(transcript_segments):
        segment_id = classifier_results[i].get("segment_id", i)
        
        # Build segment input for Langflow
        segment_input = json.dumps({{
            "text": segment.get("text", ""),
            "topic": classifier_results[i].get("topic", ""),
            "tone": classifier_results[i].get("tone", "")
        }})
        
        # Call Langflow {display_name} chain
        try:
            result = call_langflow_chain("{persona_id}_chain", segment_input)
            logger.info(f"{display_name} evaluation for segment {{segment_id}}: {{result}}")
        except Exception as e:
            logger.error(f"Error calling {display_name} Langflow chain for segment {{segment_id}}: {{e}}")
            # Fallback to default response on error
            result = {{
                "score": 3,
                "opinion": "Unable to evaluate",
                "rationale": f"Error: {{str(e)}}",
                "confidence": 0.0,
                "note": "Langflow call failed"
            }}
        
        # Store feedback with segment ID
        feedback.append({{
            "segment_id": segment_id,
            "{persona_id}": result
        }})
        
        # Store individual segment feedback in Redis
        redis_conn.set(
            f"persona_feedback:{persona_id}:{{audio_id}}:{{segment_id}}",
            json.dumps(result),
            ex=86400
        )
    
    # Store aggregated feedback
    redis_conn.set(
        f"persona_feedback:{persona_id}:{{audio_id}}",
        json.dumps(feedback),
        ex=86400
    )
    
    return feedback
'''
        
        worker_path = Path(f"app/workers/{persona_id}_worker.py")
        print(f"DEBUG: Worker path: {worker_path.absolute()}")
        with open(worker_path, 'w') as f:
            f.write(worker_template)
        print(f"DEBUG: Worker file created successfully at {worker_path}")
        
        # Clear form and redirect
        print(f"DEBUG: Persona {persona_id} created successfully!")
        return html.Div("✅ Persona created successfully! Redirecting...", style={
            "color": "#059669",
            "padding": "12px",
            "backgroundColor": "#d1fae5",
            "borderRadius": "6px",
            "border": "1px solid #059669"
        }), "", "", "", "", "", "/admin"
        
    except Exception as e:
        return html.Div(f"❌ Error creating persona: {str(e)}", style={
            "color": "#dc2626",
            "padding": "12px",
            "backgroundColor": "#fee2e2",
            "borderRadius": "6px",
            "border": "1px solid #dc2626"
        }), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Clientside callback to update current time from audio player
app.clientside_callback(
    """
    function(n_intervals) {
        const audioElement = document.getElementById('audio-player');
        
        if (audioElement && audioElement.currentTime !== undefined && !isNaN(audioElement.currentTime)) {
            console.log('[CLIENTSIDE] Current time:', audioElement.currentTime);
            return audioElement.currentTime;
        }
        
        console.log('[CLIENTSIDE] Audio element not ready or no time');
        return window.dash_clientside.no_update;
    }
    """,
    Output('current-time-store', 'data'),
    Input('playback-sync', 'n_intervals'),
    prevent_initial_call=True
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
    Output('user-clicked', 'data', allow_duplicate=True),
    Input('waveform-graph', 'clickData'),
    prevent_initial_call=True
)

# Callback 1: Auto-update waveform and metadata during playback
@app.callback(
    Output("waveform-graph", "figure", allow_duplicate=True),
    Output("segment-metadata", "children", allow_duplicate=True),
    Output("user-clicked", "data", allow_duplicate=True),
    Input('current-time-store', 'data'),
    State("segments-store", "data"),
    State("waveform-data-store", "data"),
    State("user-clicked", "data"),
    State("current-audio-id", "data"),
    prevent_initial_call=True
)
def auto_update_playback(current_time, segments, waveform_data, user_clicked, audio_id):
    import numpy as np
    
    print(f"[AUTO_UPDATE] Called! time={current_time}, clicked={user_clicked}, has_segments={bool(segments)}, has_waveform={bool(waveform_data)}")
    
    # If user just clicked, reset flag and don't update
    if user_clicked:
        print("[AUTO_UPDATE] User clicked, skipping")
        return dash.no_update, dash.no_update, False
    
    # Skip if no valid time or segments
    if current_time is None or current_time < 0 or not segments or not waveform_data:
        print(f"[AUTO_UPDATE] Skipping - invalid data")
        return dash.no_update, dash.no_update, False
    
    # Convert waveform data back to numpy arrays
    time = np.array(waveform_data['time'])
    amplitude = np.array(waveform_data['amplitude'])
    
    # Find active segment
    active_segment = next(
        (seg for seg in segments if seg["start"] <= current_time <= seg["end"]),
        None
    )
    
    # Update waveform with cursor
    fig = render_waveform_with_highlight(time, amplitude, segments, cursor_position=current_time)
    
    # Update metadata
    if active_segment:
        metadata = render_metadata_panel(active_segment)
        return fig, metadata, False
    else:
        return fig, dash.no_update, False

# Callback 2: Handle waveform clicks for seeking
@app.callback(
    Output("segment-metadata", "children"),
    Output("user-clicked", "data"),
    Input("waveform-graph", "clickData"),
    State("segments-store", "data"),
    prevent_initial_call=True
)
def handle_waveform_click(click_data, segments):
    if click_data is None or not segments:
        return dash.no_update, dash.no_update
    
    # Get clicked time from waveform
    clicked_time = click_data['points'][0]['x']
    
    # Find the segment containing this time
    active_segment = next(
        (seg for seg in segments if seg["start"] <= clicked_time <= seg["end"]),
        None
    )
    
    # Update metadata
    metadata = render_metadata_panel(active_segment) if active_segment else html.Div(
        "No segment at this time position.",
        style={"padding": "20px", "color": "#6b7280"}
    )
    
    # Set user-clicked flag
    return metadata, True

# Callback 3: Initialize metadata panel on first load
@app.callback(
    Output("segment-metadata", "children", allow_duplicate=True),
    Input("segments-store", "data"),
    prevent_initial_call='initial_duplicate'
)
def initialize_metadata(segments):
    if segments and len(segments) > 0:
        return render_metadata_panel(segments[0])
    else:
        return html.Div(
            "No segments available for this audio file.",
            style={"padding": "20px", "color": "#6b7280", "textAlign": "center"}
        )

if __name__ == "__main__":
    print(f"\n🚀 Starting dashboard server...")
    import os
    port = int(os.getenv('PORT', 5000))
    print(f"📁 Browse audio files at: http://localhost:{port}/files")
    print(f"📊 Dashboard will load dynamically from Files page")
    print(f"\nPress Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=port)
