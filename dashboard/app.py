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
app = Dash(__name__, assets_folder='assets', suppress_callback_exceptions=True)

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


def render_dashboard_page(audio_id):
    """Render the main dashboard page for a specific audio file"""
    audio_path = f"uploads/{audio_id}.wav"
    
    # Check if file exists
    if not Path(audio_path).exists():
        return html.Div([
            html.H1("⚠️ Audio File Not Found"),
            html.P(f"Audio ID: {audio_id}"),
            html.P("This audio file does not exist in the uploads folder."),
            html.A("← Back to Files", href="/files", style={
                "color": "#3b82f6",
                "textDecoration": "none"
            })
        ], style={"padding": "40px"})
    
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
    
    # Return dashboard layout
    return html.Div([
        # Header with navigation
        html.Div([
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
        dcc.Store(id='current-audio-id', data=audio_id),
    ])

# Main app layout with routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
], style={
    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    "backgroundColor": "#f3f4f6",
    "minHeight": "100vh"
})

# Routing callback
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    Input('url', 'search')
)
def display_page(pathname, search):
    """Route to the appropriate page based on pathname and query parameters"""
    print(f"[ROUTING] pathname={pathname}, search={search}")
    
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
    
    print(f"[ROUTING FIXED] pathname={pathname}, search={search}")
    
    if pathname == '/admin':
        # Admin page
        return html.Div([
            html.Div([
                html.H1("🎵 SonicLayer AI", style={
                    "margin": "0",
                    "color": "#111827",
                    "fontSize": "28px"
                }),
                render_navigation("/admin")
            ], style={
                "padding": "20px",
                "backgroundColor": "#ffffff",
                "borderBottom": "2px solid #e5e7eb",
                "marginBottom": "20px",
                "position": "relative"
            }),
            render_admin_page()
        ])
    
    elif pathname == '/files' or pathname == '/':
        # File browser page
        return html.Div([
            html.Div([
                html.H1("🎵 SonicLayer AI", style={
                    "margin": "0",
                    "color": "#111827",
                    "fontSize": "28px"
                }),
                render_navigation("/files")
            ], style={
                "padding": "20px",
                "backgroundColor": "#ffffff",
                "borderBottom": "2px solid #e5e7eb",
                "marginBottom": "20px",
                "position": "relative"
            }),
            render_file_browser()
        ])
    
    elif pathname == '/dashboard':
        # Dashboard page - get audio_id from query string
        from urllib.parse import parse_qs
        
        audio_id = default_audio_id  # Default
        if search:
            params = parse_qs(search.lstrip('?'))
            if 'audio_id' in params:
                audio_id = params['audio_id'][0]
        
        return render_dashboard_page(audio_id)
    
    else:
        # Default to file browser
        return html.Div([
            html.Div([
                html.H1("🎵 SonicLayer AI", style={
                    "margin": "0",
                    "color": "#111827",
                    "fontSize": "28px"
                }),
                render_navigation("/files")
            ], style={
                "padding": "20px",
                "backgroundColor": "#ffffff",
                "borderBottom": "2px solid #e5e7eb",
                "marginBottom": "20px",
                "position": "relative"
            }),
            render_file_browser()
        ])

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
        
        if (audioElement && audioElement.currentTime !== undefined) {
            return audioElement.currentTime;
        }
        
        return 0;
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
    Output('audio-player', 'id'),  # Dummy output (we just need to trigger on click)
    Input('waveform-graph', 'clickData'),
    prevent_initial_call=True
)

# TODO: Re-enable these interactive callbacks after refactoring for dynamic audio loading
# They currently reference module-level segments/time/amplitude that don't exist anymore

# # Global state to track current segment
# _current_segment_index = -1

# # Callback 1: Auto-update waveform and metadata during playback
# @app.callback(
#     Output("waveform-graph", "figure"),
#     Output("segment-metadata", "children", allow_duplicate=True),
#     Output("user-clicked", "data", allow_duplicate=True),
#     Input('current-time-store', 'data'),
#     State("user-clicked", "data"),
#     prevent_initial_call=True
# )
# def auto_update_playback(current_time, user_clicked):
#     global _current_segment_index
#     
#     # If user just clicked, reset flag and return
#     if user_clicked:
#         return dash.no_update, dash.no_update, False
#     
#     # Skip if no valid time
#     if current_time is None or current_time < 0:
#         return dash.no_update, dash.no_update, False
#     
#     # Find active segment
#     active_segment = None
#     active_index = -1
#     for i, seg in enumerate(segments):
#         if seg["start"] <= current_time <= seg["end"]:
#             active_segment = seg
#             active_index = i
#             break
#     
#     # No matching segment
#     if not active_segment:
#         return dash.no_update, dash.no_update, False
#     
#     # Only update metadata if we crossed into a new segment
#     if active_index != _current_segment_index:
#         _current_segment_index = active_index
#         # Update waveform cursor and metadata
#         fig = render_waveform_with_highlight(time, amplitude, segments, cursor_position=current_time)
#         metadata = render_metadata_panel(active_segment)
#         return fig, metadata, False
#     else:
#         # Same segment - just update cursor, no metadata change
#         fig = render_waveform_with_highlight(time, amplitude, segments, cursor_position=current_time)
#         return fig, dash.no_update, False

# # Callback 2: Handle waveform clicks for seeking
# @app.callback(
#     Output("segment-metadata", "children"),
#     Output("user-clicked", "data"),
#     Input("waveform-graph", "clickData"),
#     prevent_initial_call=True
# )
# def handle_waveform_click(click_data):
#     if click_data is None:
#         return dash.no_update, dash.no_update
#     
#     # Get clicked time from waveform
#     clicked_time = click_data['points'][0]['x']
#     
#     # Find the segment containing this time
#     active_segment = next(
#         (seg for seg in segments if seg["start"] <= clicked_time <= seg["end"]),
#         None
#     )
#     
#     # Update metadata
#     metadata = render_metadata_panel(active_segment) if active_segment else "No segment at this time position."
#     
#     # Seek player to clicked time and set user-clicked flag
#     return metadata, True

# # Callback 3: Initialize metadata panel on first load
# @app.callback(
#     Output("segment-metadata", "children", allow_duplicate=True),
#     Input("waveform-graph", "id"),
#     prevent_initial_call='initial_duplicate'
# )
# def initialize_metadata(_):
#     return render_metadata_panel(segments[0]) if segments else "No segments available."

if __name__ == "__main__":
    print(f"\n🚀 Starting dashboard server...")
    import os
    port = int(os.getenv('PORT', 5000))
    print(f"📁 Browse audio files at: http://localhost:{port}/files")
    print(f"📊 Dashboard will load dynamically from Files page")
    print(f"\nPress Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=port)
