from dash import Dash, Input, Output, State, dcc, html, dash, ALL, callback_context
import sys
import json
from pathlib import Path
from components.waveform import render_waveform_with_highlight
from components.audio_player import render_audio_player
from components.metadata_panel import render_metadata_panel
from components.admin_page import render_admin_page
from services.audio_utils import extract_waveform
from services.api_client import fetch_segments
from utils.audio_scanner import get_all_audio_files

# Get default audio_id from command line (for backwards compatibility)
default_audio_id = sys.argv[1] if len(sys.argv) > 1 else None

print(f"Dashboard server starting...")
if default_audio_id:
    print(f"Default audio (command-line): {default_audio_id}")
else:
    print("No default audio - use file browser to select")

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


def create_file_sidebar():
    """Create the left sidebar with file browser."""
    audio_files = get_all_audio_files()
    
    if not audio_files:
        dropdown_options = []
        dropdown_value = None
        file_info = html.Div("No audio files found", style={"padding": "10px", "color": "#6b7280", "fontSize": "13px"})
    else:
        # Create dropdown options from audio files
        dropdown_options = [
            {
                "label": f"🎵 {audio['audio_id'][:16]}... ({audio['num_segments']} segments)",
                "value": audio["audio_id"]
            }
            for audio in audio_files
        ]
        dropdown_value = default_audio_id if default_audio_id else None
        file_info = html.Div(f"{len(audio_files)} file{'s' if len(audio_files) != 1 else ''} available", 
                            style={"padding": "10px", "color": "#6b7280", "fontSize": "13px"})
    
    return html.Div([
        html.H3("📁 Audio Files", style={
            "margin": "0 0 16px 0",
            "fontSize": "16px",
            "color": "#111827"
        }),
        dcc.Dropdown(
            id="audio-file-selector",
            options=dropdown_options,
            value=dropdown_value,
            placeholder="Select an audio file...",
            style={"marginBottom": "10px"}
        ),
        file_info
    ], style={
        "width": "300px",
        "backgroundColor": "#ffffff",
        "borderRight": "2px solid #e5e7eb",
        "padding": "20px",
        "overflowY": "auto",
        "height": "100vh",
        "position": "fixed",
        "left": "0",
        "top": "0"
    })


# Main app layout - single page with all components at top level
app.layout = html.Div([
    # Left sidebar - file browser
    create_file_sidebar(),
    
    # Main content area (with left margin for sidebar)
    html.Div([
        # Header
        html.Div([
            html.Div([
                html.H1("🎵 SonicLayer AI - Audio Analysis Dashboard", style={
                    "margin": "0",
                    "color": "#111827",
                    "fontSize": "28px"
                }),
                html.P(id="dashboard-audio-id-display", children="Select an audio file from the sidebar", style={
                    "margin": "4px 0 0 0",
                    "color": "#6b7280",
                    "fontSize": "14px"
                })
            ]),
            html.Div([
                html.Button("⚙️ Admin", id="admin-toggle-btn", n_clicks=0, style={
                    "padding": "8px 16px",
                    "borderRadius": "6px",
                    "border": "1px solid #e5e7eb",
                    "backgroundColor": "#ffffff",
                    "color": "#374151",
                    "fontWeight": "500",
                    "fontSize": "14px",
                    "cursor": "pointer"
                })
            ], style={
                "position": "absolute",
                "top": "20px",
                "right": "20px"
            })
        ], style={
            "padding": "20px",
            "backgroundColor": "#ffffff",
            "borderBottom": "2px solid #e5e7eb",
            "marginBottom": "20px",
            "position": "relative"
        }),
        
        # Main content - two columns
        html.Div([
            # Left column - Waveform and audio player
            html.Div([
                html.Div(id="audio-player-container", children=html.Div(
                    "Select an audio file to begin",
                    style={"padding": "20px", "color": "#6b7280", "textAlign": "center"}
                )),
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
                children=html.Div("Select an audio file to view analysis", style={"padding": "20px", "color": "#6b7280"}),
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
        dcc.Store(id='current-audio-id', data=default_audio_id),
        dcc.Store(id='segments-store', data=[]),
        dcc.Store(id='waveform-data-store', data={'time': [], 'amplitude': []}),
        dcc.Store(id='waveform-click-dummy', data=None),  # Dummy store for clientside callback
    ], style={
        "marginLeft": "300px",  # Offset for fixed sidebar
        "minHeight": "100vh"
    }),
    
    # Admin modal overlay (hidden by default)
    html.Div([
        html.Div([
            html.Div([
                html.H2("⚙️ Admin Panel", style={"margin": "0 0 20px 0"}),
                html.Button("✕ Close", id="admin-close-btn", n_clicks=0, style={
                    "position": "absolute",
                    "top": "20px",
                    "right": "20px",
                    "padding": "8px 16px",
                    "borderRadius": "6px",
                    "border": "1px solid #e5e7eb",
                    "backgroundColor": "#ffffff",
                    "cursor": "pointer"
                }),
                render_admin_page()
            ], style={
                "backgroundColor": "#ffffff",
                "borderRadius": "8px",
                "padding": "30px",
                "maxWidth": "800px",
                "maxHeight": "90vh",
                "overflowY": "auto",
                "position": "relative"
            })
        ], style={
            "position": "fixed",
            "top": "0",
            "left": "0",
            "width": "100%",
            "height": "100%",
            "backgroundColor": "rgba(0,0,0,0.5)",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "zIndex": "1000"
        })
    ], id="admin-modal", style={"display": "none"})
    
], style={
    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    "backgroundColor": "#f3f4f6"
})


# Callback 1: Toggle admin modal
@app.callback(
    Output('admin-modal', 'style'),
    Input('admin-toggle-btn', 'n_clicks'),
    Input('admin-close-btn', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_admin_modal(open_clicks, close_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return {"display": "none"}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'admin-toggle-btn':
        return {"display": "block"}
    else:
        return {"display": "none"}


# Callback 2: Handle file selection and load data
@app.callback(
    Output('current-audio-id', 'data'),
    Output('segments-store', 'data'),
    Output('waveform-data-store', 'data'),
    Output('audio-player-container', 'children'),
    Output('waveform-graph', 'figure', allow_duplicate=True),
    Output('dashboard-audio-id-display', 'children'),
    Output('segment-metadata', 'children', allow_duplicate=True),
    Input('audio-file-selector', 'value'),
    prevent_initial_call='initial_duplicate'
)
def load_audio_file(audio_id):
    import numpy as np
    
    print(f"[LOAD_AUDIO] Selected audio_id: {audio_id}")
    
    # If no audio selected, use default
    if not audio_id:
        audio_id = default_audio_id
    
    # If still no audio_id, return empty state
    if not audio_id:
        return (
            None,
            [],
            {'time': [], 'amplitude': []},
            html.Div("Select an audio file to begin", style={"padding": "20px", "color": "#6b7280", "textAlign": "center"}),
            {},
            "Select an audio file from the sidebar",
            html.Div("Select an audio file to view analysis", style={"padding": "20px", "color": "#6b7280"})
        )
    
    # Load audio data
    audio_path = f"uploads/{audio_id}.wav"
    if not Path(audio_path).exists():
        print(f"Audio file not found: {audio_path}")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    print(f"Loading audio data for: {audio_id}")
    
    # Extract waveform
    time, amplitude = extract_waveform(audio_path)
    
    # Fetch segments
    segments = fetch_segments(audio_id)
    print(f"Loaded {len(segments)} segments")
    
    # Create audio player
    player = render_audio_player(audio_id)
    
    # Create initial waveform
    fig = render_waveform_with_highlight(time, amplitude, segments)
    
    # Display text
    display_text = f"Audio ID: {audio_id[:16]}..."
    
    # Initial metadata (first segment)
    if segments and len(segments) > 0:
        metadata = render_metadata_panel(segments[0])
    else:
        metadata = html.Div("No segments available", style={"padding": "20px", "color": "#6b7280"})
    
    return (
        audio_id,
        segments,
        {'time': time.tolist(), 'amplitude': amplitude.tolist()},
        player,
        fig,
        display_text,
        metadata
    )


# Callback 3: Persona creation
@app.callback(
    Output('creation-feedback', 'children'),
    Output('persona-id-input', 'value'),
    Output('persona-name-input', 'value'),
    Output('persona-emoji-input', 'value'),
    Output('persona-description-input', 'value'),
    Output('persona-prompt-input', 'value'),
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
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Validate inputs
    if not persona_id or not display_name or not prompt_json:
        return html.Div("❌ Please fill in all required fields (*)", style={
            "color": "#dc2626",
            "padding": "12px",
            "backgroundColor": "#fee2e2",
            "borderRadius": "6px",
            "border": "1px solid #dc2626"
        }), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Validate persona_id format (lowercase, no spaces)
    if not persona_id.replace('_', '').isalnum() or persona_id != persona_id.lower():
        return html.Div("❌ Persona ID must be lowercase alphanumeric (underscores allowed)", style={
            "color": "#dc2626",
            "padding": "12px",
            "backgroundColor": "#fee2e2",
            "borderRadius": "6px",
            "border": "1px solid #dc2626"
        }), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Parse JSON
    try:
        parsed_prompt = json.loads(prompt_json)
    except:
        parsed_prompt = {
            "system": prompt_json,
            "user_template": "Evaluate: {text}"
        }
    
    # Save persona to config files
    try:
        # Add to backend config
        backend_config_path = Path("app/config/personas.py")
        dashboard_config_path = Path("dashboard/personas_config.py")
        langflow_config_path = Path("app/services/langflow_client.py")
        
        # Read backend config
        with open(backend_config_path, 'r') as f:
            backend_content = f.read()
        
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
        backend_content = backend_content.replace("\n]", f",\n{new_backend_entry}\n]")
        
        # Write backend config
        with open(backend_config_path, 'w') as f:
            f.write(backend_content)
        
        # Update dashboard config
        with open(dashboard_config_path, 'r') as f:
            dashboard_content = f.read()
        
        new_dashboard_entry = f'''    {{
        "id": "{persona_id}",
        "display_name": "{display_name}",
        "emoji": "{emoji or '🎯'}",
        "description": "{description or 'Custom persona'}"
    }}'''
        
        dashboard_content = dashboard_content.replace("\n]", f",\n{new_dashboard_entry}\n]")
        
        with open(dashboard_config_path, 'w') as f:
            f.write(dashboard_content)
        
        # Update langflow prompts
        with open(langflow_config_path, 'r') as f:
            langflow_content = f.read()
        
        new_prompt_entry = f'''    "{persona_id}_chain": {json.dumps(parsed_prompt, indent=8).replace("        ", "    ")},
}}'''
        
        langflow_content = langflow_content.replace("\n}", f"\n{new_prompt_entry}")
        
        with open(langflow_config_path, 'w') as f:
            f.write(langflow_content)
        
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
        with open(worker_path, 'w') as f:
            f.write(worker_template)
        
        # Clear form
        return html.Div("✅ Persona created successfully!", style={
            "color": "#059669",
            "padding": "12px",
            "backgroundColor": "#d1fae5",
            "borderRadius": "6px",
            "border": "1px solid #059669"
        }), "", "", "", "", ""
        
    except Exception as e:
        return html.Div(f"❌ Error creating persona: {str(e)}", style={
            "color": "#dc2626",
            "padding": "12px",
            "backgroundColor": "#fee2e2",
            "borderRadius": "6px",
            "border": "1px solid #dc2626"
        }), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# Clientside callback to update current time from audio player
app.clientside_callback(
    """
    function(n_intervals) {
        const audioElement = document.getElementById('audio-player');
        
        if (audioElement && audioElement.currentTime !== undefined && !isNaN(audioElement.currentTime)) {
            return audioElement.currentTime;
        }
        
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
    Output('waveform-click-dummy', 'data', allow_duplicate=True),
    Input('waveform-graph', 'clickData'),
    prevent_initial_call=True
)


# Callback 4: Auto-update waveform and metadata during playback (THE CORE FEATURE)
@app.callback(
    Output("waveform-graph", "figure", allow_duplicate=True),
    Output("segment-metadata", "children", allow_duplicate=True),
    Output("user-clicked", "data", allow_duplicate=True),
    Input('current-time-store', 'data'),
    State("segments-store", "data"),
    State("waveform-data-store", "data"),
    State("user-clicked", "data"),
    prevent_initial_call=True
)
def auto_update_playback(current_time, segments, waveform_data, user_clicked):
    import numpy as np
    
    print(f"[AUTO_UPDATE] time={current_time}, segments={len(segments) if segments else 0}")
    
    # If user just clicked, reset flag and don't update
    if user_clicked:
        return dash.no_update, dash.no_update, False
    
    # Skip if no valid time or segments
    if current_time is None or current_time < 0 or not segments or not waveform_data or not waveform_data.get('time'):
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


# Callback 5: Handle waveform clicks for seeking (note: clientside callback handles audio seeking)
@app.callback(
    Output("segment-metadata", "children", allow_duplicate=True),
    Output("user-clicked", "data", allow_duplicate=True),
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


if __name__ == "__main__":
    print(f"\n🚀 Starting dashboard server...")
    print(f"📊 Dashboard available at: http://0.0.0.0:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
