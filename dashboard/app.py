from dash import Dash, Input, Output, State, dcc, html, dash, ALL, callback_context, MATCH
from dash.exceptions import PreventUpdate
import sys
import json
from pathlib import Path
from components.waveform import render_waveform_with_highlight
from components.audio_player import render_audio_player
from components.metadata_panel import render_metadata_panel
from components.admin_page import render_admin_page
from components.summary_panel import render_collapsible_summary, render_detailed_summary
from services.audio_utils import extract_waveform
from services.api_client import fetch_segments
from utils.audio_scanner import get_all_audio_files
from personas_config import get_all_personas

# Import persona prompts from langflow_client for editing
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
from services.langflow_client import PERSONA_PROMPTS

# Get default audio_id from command line (for backwards compatibility)
default_audio_id = sys.argv[1] if len(sys.argv) > 1 else None

print(f"Dashboard server starting...")
if default_audio_id:
    print(f"Default audio (command-line): {default_audio_id}")
else:
    print("No default audio - use file browser to select")

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


def get_score_color(score):
    """Get color for score badge based on value."""
    if score >= 4.0:
        return "#10b981"  # Green - Excellent
    elif score >= 3.0:
        return "#3b82f6"  # Blue - Good
    elif score >= 2.0:
        return "#f59e0b"  # Orange - Moderate
    else:
        return "#ef4444"  # Red - Low


def create_file_sidebar():
    """Create the left sidebar with clickable file browser."""
    audio_files = get_all_audio_files()  # Already includes summary data
    personas = get_all_personas()
    
    if not audio_files:
        file_list = html.Div(
            "No audio files found",
            style={
                "padding": "20px",
                "color": "#6b7280",
                "fontSize": "14px",
                "textAlign": "center"
            }
        )
    else:
        # Create clickable file items - each outputs to the same hidden store
        file_items = []
        for i, audio in enumerate(audio_files):
            short_id = audio["audio_id"][:12] + "..."
            is_selected = audio["audio_id"] == default_audio_id
            
            # Build badges from pre-fetched summary (no HTTP calls!)
            summary_badges = []
            if audio.get("summary"):
                for persona in personas:
                    persona_id = persona["id"]
                    if persona_id in audio["summary"]:
                        mini_stats = audio["summary"][persona_id]
                        emoji = mini_stats["emoji"]
                        avg_score = mini_stats["avg_score"]
                        
                        badge = html.Span([
                            html.Span(emoji, style={"marginRight": "3px", "fontSize": "11px"}),
                            html.Span(f"{avg_score:.1f}", style={
                                "fontWeight": "500",
                                "fontSize": "11px"
                            })
                        ], style={
                            "display": "inline-block",
                            "padding": "2px 6px",
                            "marginRight": "4px",
                            "fontSize": "11px",
                            "borderRadius": "3px",
                            "backgroundColor": "#fafafa",  # Subtle gray background
                            "color": "#64748b",  # slate-500
                            "border": "none"  # No borders - minimal design
                        })
                        summary_badges.append(badge)
            
            item = html.Button([
                html.Div([
                    html.Div(short_id, style={
                        "fontSize": "13px",
                        "fontWeight": "500",
                        "color": "#0f172a" if not is_selected else "#0f172a",  # slate-900
                        "marginBottom": "4px"
                    }),
                    html.Div(f"{audio['num_segments']} segments", style={
                        "fontSize": "12px",
                        "color": "#94a3b8",  # slate-400
                        "marginBottom": "6px" if summary_badges else "0"
                    }),
                    html.Div(summary_badges, style={
                        "display": "flex",
                        "flexWrap": "wrap",
                        "gap": "3px"
                    }) if summary_badges else None
                ], style={
                    "flex": "1",
                    "textAlign": "left"
                })
            ], 
            id=f"file-btn-{i}",
            n_clicks=0,
            **{"data-audio-id": audio["audio_id"]},  # Store audio_id in data attribute
            style={
                "display": "flex",
                "alignItems": "flex-start",
                "width": "100%",
                "padding": "12px",
                "marginBottom": "4px",
                "backgroundColor": "#fafafa" if is_selected else "transparent",  # Minimal background
                "border": "none",  # NO borders - extreme minimalism
                "borderLeft": f"2px solid {'#0f172a' if is_selected else 'transparent'}",  # Subtle left accent only
                "borderRadius": "0",  # No rounded corners
                "cursor": "pointer",
                "textAlign": "left",
                "transition": "all 0.15s ease",
                "boxShadow": "none"  # NO shadows
            })
            
            file_items.append(item)
        
        file_list = html.Div(file_items, id="file-list-container")
    
    return html.Div([
        html.H3([
            html.Span("Audio Files", style={
                "fontWeight": "500",
                "fontSize": "13px",
                "color": "#0f172a",  # slate-900
                "textTransform": "uppercase",
                "letterSpacing": "0.05em"
            }),
            html.Span(f" {len(audio_files)}", style={
                "fontWeight": "400",
                "fontSize": "13px",
                "color": "#94a3b8",  # slate-400
                "marginLeft": "6px"
            }) if audio_files else ""
        ], style={"margin": "0 0 20px 0"}),
        file_list,
        dcc.Store(id="selected-audio-store", data=default_audio_id)  # Hidden store for selected file
    ], style={
        "width": "280px",
        "backgroundColor": "#ffffff",
        "borderRight": "1px solid #f1f5f9",  # slate-100
        "padding": "20px 16px",
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
        # Extreme Minimal Header
        html.Div([
            # Left section - title and audio ID inline
            html.Div([
                html.Span("SonicLayer AI", style={
                    "fontSize": "14px",
                    "fontWeight": "500",
                    "color": "#0f172a",  # slate-900
                    "marginRight": "12px"
                }),
                html.Span("·", style={
                    "fontSize": "14px",
                    "color": "#cbd5e1",  # slate-300
                    "marginRight": "12px"
                }),
                html.Span(id="dashboard-audio-id-display", children="Select a file", style={
                    "fontSize": "13px",
                    "color": "#94a3b8",  # slate-400
                    "fontWeight": "400",
                    "maxWidth": "300px",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap",
                    "display": "inline-block"
                })
            ], style={
                "display": "flex",
                "alignItems": "center"
            }),
            # Right section - admin button
            html.Div([
                html.Button("Admin", id="admin-toggle-btn", n_clicks=0, style={
                    "padding": "6px 12px",
                    "borderRadius": "4px",
                    "border": "1px solid #f1f5f9",  # slate-100
                    "backgroundColor": "#ffffff",
                    "color": "#64748b",  # slate-500
                    "fontWeight": "400",
                    "fontSize": "13px",
                    "cursor": "pointer",
                    "transition": "all 0.15s ease"
                })
            ])
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "16px 32px",
            "backgroundColor": "#ffffff",  # Pure white
            "borderBottom": "1px solid #f1f5f9"  # slate-100 - subtle separator
        }),
        
        # Tabs for different views - Extreme minimal styling
        dcc.Tabs(id="main-tabs", value="analysis-tab", 
            style={
                "borderBottom": "1px solid #f1f5f9",  # slate-100
                "backgroundColor": "#ffffff"
            },
            children=[
            # Tab 1: Analysis View (current waveform + metadata)
            dcc.Tab(label="Analysis", value="analysis-tab", 
                style={
                    "padding": "12px 20px",
                    "fontSize": "13px",
                    "fontWeight": "400",
                    "color": "#94a3b8",  # slate-400
                    "border": "none",
                    "borderBottom": "2px solid transparent",
                    "backgroundColor": "transparent"
                },
                selected_style={
                    "padding": "12px 20px",
                    "fontSize": "13px",
                    "fontWeight": "500",
                    "color": "#0f172a",  # slate-900
                    "border": "none",
                    "borderBottom": "2px solid #0f172a",  # slate-900
                    "backgroundColor": "transparent"
                },
                children=[
                html.Div([
                    # Left column - Waveform and audio player
                    html.Div([
                        # Collapsible summary panel (Phase 3)
                        html.Div(id="summary-panel-container", children=html.Div(
                            "Loading summary...",
                            style={"padding": "20px", "color": "#94a3b8", "fontStyle": "normal", "fontSize": "13px"}
                        )),
                        
                        html.Div(id="audio-player-container", children=html.Div(
                            "Select an audio file to begin",
                            style={"padding": "32px 20px", "color": "#94a3b8", "textAlign": "center", "fontSize": "13px"}
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
                        children=html.Div("Select an audio file to view analysis", style={
                            "padding": "32px 20px",
                            "color": "#94a3b8",
                            "fontSize": "13px"
                        }),
                        style={
                            "width": "450px",
                            "backgroundColor": "#ffffff",
                            "borderRadius": "0",  # No rounded corners
                            "border": "1px solid #f1f5f9",  # slate-100
                            "maxHeight": "600px",
                            "overflowY": "auto",
                            "boxShadow": "none"  # NO shadows
                        }
                    )
                ], style={
                    "display": "flex",
                    "padding": "32px",  # Generous whitespace
                    "gap": "32px"  # Large gap between columns
                })
            ]),
            
            # Tab 2: Summary View (new aggregated stats)
            dcc.Tab(label="Summary", value="summary-tab",
                style={
                    "padding": "12px 20px",
                    "fontSize": "13px",
                    "fontWeight": "400",
                    "color": "#94a3b8",  # slate-400
                    "border": "none",
                    "borderBottom": "2px solid transparent",
                    "backgroundColor": "transparent"
                },
                selected_style={
                    "padding": "12px 20px",
                    "fontSize": "13px",
                    "fontWeight": "500",
                    "color": "#0f172a",  # slate-900
                    "border": "none",
                    "borderBottom": "2px solid #0f172a",  # slate-900
                    "backgroundColor": "transparent"
                },
                children=[
                html.Div(
                    id="summary-content",
                    children=html.Div(
                        "Select an audio file to view summary",
                        style={
                            "padding": "80px 32px",
                            "color": "#94a3b8",  # slate-400
                            "textAlign": "center",
                            "fontSize": "13px"
                        }
                    ),
                    style={"padding": "32px"}  # Generous padding
                )
            ])
        ]),
        
        # Hidden components for state management
        dcc.Interval(id="playback-sync", interval=1000, n_intervals=0),  # Update every second
        dcc.Store(id="user-clicked", data=False),
        dcc.Store(id='current-time-store', data=0),
        dcc.Store(id='current-audio-id', data=default_audio_id),
        dcc.Store(id='segments-store', data=[]),
        dcc.Store(id='waveform-data-store', data={'time': [], 'amplitude': []}),
        dcc.Store(id='waveform-click-dummy', data=None),  # Dummy store for clientside callback
        dcc.Store(id='summary-data-store', data=None),  # Store for summary data (Phase 3)
        dcc.Store(id='summary-collapsed', data=False),  # Store for collapse state
    ], style={
        "marginLeft": "280px",  # Offset for fixed sidebar
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


# Callback 6: Render and update persona cards with edit capability
@app.callback(
    Output('personas-list', 'children'),
    Input('editing-persona-id', 'data'),
    prevent_initial_call=False  # Render on initial load
)
def render_persona_cards(editing_id):
    """Render persona cards, expanding the one being edited."""
    personas = get_all_personas()
    cards = []
    
    for persona in personas:
        persona_id = persona['id']
        is_editing = (editing_id == persona_id)
        
        # Map persona ID to chain name (e.g., "genz" -> "genz_chain")
        chain_name = f"{persona_id}_chain"
        
        if is_editing:
            # EXPANDED: Show edit form
            # Load current prompts from langflow_client.py
            current_prompts = PERSONA_PROMPTS.get(chain_name, {
                "system": "",
                "user_template": ""
            })
            
            card = html.Div([
                # Header with persona info
                html.Div([
                    html.Span(persona['emoji'], style={
                        "fontSize": "24px",
                        "marginRight": "12px"
                    }),
                    html.Strong(f"Editing: {persona['display_name']}", style={
                        "fontSize": "16px",
                        "color": "#3b82f6"
                    })
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginBottom": "16px",
                    "paddingBottom": "12px",
                    "borderBottom": "2px solid #e5e7eb"
                }),
                
                # Edit form fields
                html.Div([
                    # Display Name
                    html.Label("Display Name:", style={"fontWeight": "500", "fontSize": "13px", "marginBottom": "4px", "display": "block"}),
                    dcc.Input(
                        id={'type': 'edit-name', 'id': persona_id},
                        value=persona['display_name'],
                        style={
                            "width": "100%",
                            "padding": "8px",
                            "marginBottom": "12px",
                            "border": "1px solid #d1d5db",
                            "borderRadius": "4px",
                            "boxSizing": "border-box"
                        }
                    ),
                    
                    # Emoji
                    html.Label("Emoji:", style={"fontWeight": "500", "fontSize": "13px", "marginBottom": "4px", "display": "block"}),
                    dcc.Input(
                        id={'type': 'edit-emoji', 'id': persona_id},
                        value=persona['emoji'],
                        maxLength=2,
                        style={
                            "width": "100%",
                            "padding": "8px",
                            "marginBottom": "12px",
                            "border": "1px solid #d1d5db",
                            "borderRadius": "4px",
                            "boxSizing": "border-box"
                        }
                    ),
                    
                    # Description
                    html.Label("Description:", style={"fontWeight": "500", "fontSize": "13px", "marginBottom": "4px", "display": "block"}),
                    dcc.Input(
                        id={'type': 'edit-description', 'id': persona_id},
                        value=persona.get('description', ''),
                        style={
                            "width": "100%",
                            "padding": "8px",
                            "marginBottom": "12px",
                            "border": "1px solid #d1d5db",
                            "borderRadius": "4px",
                            "boxSizing": "border-box"
                        }
                    ),
                    
                    # System Prompt
                    html.Label("System Prompt:", style={"fontWeight": "500", "fontSize": "13px", "marginBottom": "4px", "display": "block"}),
                    dcc.Textarea(
                        id={'type': 'edit-system-prompt', 'id': persona_id},
                        value=current_prompts.get('system', ''),
                        style={
                            "width": "100%",
                            "height": "120px",
                            "padding": "8px",
                            "marginBottom": "12px",
                            "border": "1px solid #d1d5db",
                            "borderRadius": "4px",
                            "fontFamily": "monospace",
                            "fontSize": "12px",
                            "boxSizing": "border-box",
                            "resize": "vertical"
                        }
                    ),
                    
                    # User Template Prompt
                    html.Label("User Template:", style={"fontWeight": "500", "fontSize": "13px", "marginBottom": "4px", "display": "block"}),
                    dcc.Textarea(
                        id={'type': 'edit-user-template', 'id': persona_id},
                        value=current_prompts.get('user_template', ''),
                        style={
                            "width": "100%",
                            "height": "120px",
                            "padding": "8px",
                            "marginBottom": "16px",
                            "border": "1px solid #d1d5db",
                            "borderRadius": "4px",
                            "fontFamily": "monospace",
                            "fontSize": "12px",
                            "boxSizing": "border-box",
                            "resize": "vertical"
                        }
                    ),
                    
                    # Action buttons
                    html.Div([
                        html.Button(
                            "💾 Save Changes",
                            id={'type': 'save-persona-btn', 'id': persona_id},
                            n_clicks=0,
                            style={"padding": "10px 16px", "backgroundColor": "#3b82f6", "color": "white", "border": "none", "borderRadius": "4px", "cursor": "pointer", "marginRight": "8px", "fontWeight": "500"}
                        ),
                        html.Button(
                            "✕ Cancel",
                            id={'type': 'cancel-edit-btn', 'id': persona_id},
                            n_clicks=0,
                            style={"padding": "10px 16px", "backgroundColor": "#6b7280", "color": "white", "border": "none", "borderRadius": "4px", "cursor": "pointer", "fontWeight": "500"}
                        )
                    ])
                ])
            ], style={
                "padding": "16px",
                "backgroundColor": "#eff6ff",
                "border": "2px solid #3b82f6",
                "borderRadius": "6px",
                "marginBottom": "12px"
            })
        else:
            # COLLAPSED: Show compact view with Edit button
            card = html.Div([
                html.Div([
                    html.Div([
                        html.Span(persona['emoji'], style={
                            "fontSize": "24px",
                            "marginRight": "12px"
                        }),
                        html.Div([
                            html.Strong(persona['display_name'], style={
                                "fontSize": "16px",
                                "color": "#111827",
                                "display": "block"
                            }),
                            html.Span(f"ID: {persona_id}", style={
                                "fontSize": "12px",
                                "color": "#6b7280",
                                "display": "block",
                                "marginTop": "2px"
                            }),
                            html.Span(persona.get('description', ''), style={
                                "fontSize": "13px",
                                "color": "#6b7280",
                                "display": "block",
                                "marginTop": "4px"
                            })
                        ], style={"flex": "1"})
                    ], style={
                        "display": "flex",
                        "alignItems": "flex-start",
                        "marginBottom": "12px"
                    }),
                    
                    # Edit button
                    html.Button(
                        "✏️ Edit",
                        id={'type': 'edit-persona-btn', 'id': persona_id},
                        n_clicks=0,
                        style={
                            "width": "100%",
                            "padding": "8px",
                            "backgroundColor": "#ffffff",
                            "color": "#3b82f6",
                            "border": "1px solid #3b82f6",
                            "borderRadius": "4px",
                            "cursor": "pointer",
                            "fontSize": "13px",
                            "fontWeight": "500"
                        }
                    )
                ])
            ], style={
                "padding": "16px",
                "backgroundColor": "#f9fafb",
                "border": "1px solid #e5e7eb",
                "borderRadius": "6px",
                "marginBottom": "12px"
            })
        
        cards.append(card)
    
    return cards


# Callback 7: Handle Edit button clicks to expand persona card
@app.callback(
    Output('editing-persona-id', 'data'),
    Input({'type': 'edit-persona-btn', 'id': ALL}, 'n_clicks'),
    Input({'type': 'cancel-edit-btn', 'id': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_edit_buttons(edit_clicks, cancel_clicks):
    """Handle Edit and Cancel button clicks."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id']
    
    # Extract the button type and persona ID from the triggered component
    if 'edit-persona-btn' in triggered_id:
        # Parse the ID from the pattern-matching callback
        import json as json_module
        id_str = triggered_id.split('.')[0]
        id_dict = json_module.loads(id_str)
        persona_id = id_dict['id']
        print(f"[EDIT] Opening edit mode for persona: {persona_id}")
        return persona_id
    elif 'cancel-edit-btn' in triggered_id:
        print("[EDIT] Canceling edit mode")
        return None
    
    raise PreventUpdate


# Callback 8: Handle Save button clicks to persist persona changes
@app.callback(
    Output('editing-persona-id', 'data', allow_duplicate=True),
    Output('save-toast', 'children', allow_duplicate=True),
    Output('save-toast', 'style', allow_duplicate=True),
    Input({'type': 'save-persona-btn', 'id': ALL}, 'n_clicks'),
    State({'type': 'edit-name', 'id': ALL}, 'value'),
    State({'type': 'edit-emoji', 'id': ALL}, 'value'),
    State({'type': 'edit-description', 'id': ALL}, 'value'),
    State({'type': 'edit-system-prompt', 'id': ALL}, 'value'),
    State({'type': 'edit-user-template', 'id': ALL}, 'value'),
    prevent_initial_call=True
)
def save_persona_changes(save_clicks, names, emojis, descriptions, system_prompts, user_templates):
    """Save persona changes to configuration files."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    triggered_id = ctx.triggered[0]['prop_id']
    triggered_value = ctx.triggered[0]['value']
    
    # Only proceed if Save button was actually clicked (not just rendered)
    # The value should be > 0 and the trigger should be from save button
    if 'save-persona-btn' not in triggered_id or not triggered_value:
        raise PreventUpdate
    
    # Parse which persona was saved
    import json as json_module
    id_str = triggered_id.split('.')[0]
    id_dict = json_module.loads(id_str)
    persona_id = id_dict['id']
    
    # Find the index of this persona in the ALL arrays
    # The index corresponds to the order personas appear in the cards
    personas = get_all_personas()
    persona_index = next((i for i, p in enumerate(personas) if p['id'] == persona_id), None)
    
    if persona_index is None:
        print(f"[SAVE] Error: Could not find persona {persona_id}")
        raise PreventUpdate
    
    # IMPORTANT: When only ONE persona is in edit mode, there's only ONE set of form fields
    # So we should always use index 0 for the currently-editing persona's values
    # The arrays contain values ONLY for personas in edit mode, not all personas
    new_name = names[0] if len(names) > 0 else ""
    new_emoji = emojis[0] if len(emojis) > 0 else ""
    new_description = descriptions[0] if len(descriptions) > 0 else ""
    new_system_prompt = system_prompts[0] if len(system_prompts) > 0 else ""
    new_user_template = user_templates[0] if len(user_templates) > 0 else ""
    
    # Safety check: Don't save if critical fields are empty
    if not new_name or not new_emoji:
        print(f"[SAVE] ❌ Aborted: Name or emoji is empty for {persona_id}")
        print(f"  Name: '{new_name}', Emoji: '{new_emoji}'")
        error_toast = html.Div("❌ Error: Name and emoji are required!", style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "backgroundColor": "#ef4444",
            "color": "white",
            "padding": "12px 20px",
            "borderRadius": "6px",
            "fontSize": "14px",
            "fontWeight": "500",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
            "zIndex": "10000",
            "display": "block"
        })
        return dash.no_update, error_toast, {"display": "block"}
    
    print(f"[SAVE] Saving changes for persona: {persona_id}")
    print(f"  Name: {new_name}")
    print(f"  Emoji: {new_emoji}")
    
    try:
        # Update personas_config.py
        personas_config_path = Path(__file__).parent / "personas_config.py"
        personas_content = personas_config_path.read_text()
        
        # Find and update this persona in the PERSONAS list
        # We'll do a simple find-replace approach
        personas_list = get_all_personas()
        new_personas_list = []
        
        for p in personas_list:
            if p['id'] == persona_id:
                # Update this persona
                new_personas_list.append({
                    "id": persona_id,
                    "display_name": new_name,
                    "emoji": new_emoji,
                    "description": new_description
                })
            else:
                # Keep as is
                new_personas_list.append(p)
        
        # Rewrite the personas_config.py file
        new_config_content = f'''"""
Persona configuration for dashboard.
This mirrors the configuration in app/config/personas.py
"""

PERSONAS = {json.dumps(new_personas_list, indent=4)}

def get_all_personas():
    """Get all persona configurations"""
    return PERSONAS
'''
        personas_config_path.write_text(new_config_content)
        print(f"[SAVE] Updated personas_config.py")
        
        # Update langflow_client.py
        langflow_path = Path(__file__).parent.parent / "app" / "services" / "langflow_client.py"
        langflow_content = langflow_path.read_text()
        
        # Update the PERSONA_PROMPTS dictionary for this chain
        chain_name = f"{persona_id}_chain"
        
        # Read current PERSONA_PROMPTS
        import re
        
        # Find the chain in the file and replace it
        pattern = rf'"{chain_name}":\s*{{[^}}]*"system":\s*"[^"]*"[^}}]*"user_template":\s*"""[^"""]*"""[^}}]*}}'
        
        # Create the new chain content
        new_chain = f'''"{chain_name}": {{
        "system": {json.dumps(new_system_prompt)},
        "user_template": {json.dumps(new_user_template)}
    }}'''
        
        # Try to replace using regex (but catch errors if replacement string has escape sequences)
        try:
            new_langflow_content = re.sub(pattern, new_chain, langflow_content, flags=re.DOTALL)
        except re.error:
            # Regex failed (likely due to escape sequences in replacement string)
            new_langflow_content = langflow_content
        
        # If regex didn't match or failed, use manual approach
        if new_langflow_content == langflow_content:
            # Manual replacement - find the chain and replace it
            # This is more robust for multi-line strings
            start_marker = f'"{chain_name}":'
            if start_marker in langflow_content:
                # Find start and end of this chain
                start_idx = langflow_content.find(start_marker)
                # Find the next chain or closing brace
                rest = langflow_content[start_idx:]
                # Count braces to find the end
                brace_count = 0
                end_idx = start_idx
                in_chain = False
                for i, char in enumerate(rest):
                    if char == '{':
                        brace_count += 1
                        in_chain = True
                    elif char == '}':
                        brace_count -= 1
                        if in_chain and brace_count == 0:
                            end_idx = start_idx + i + 1
                            break
                
                # Replace this section
                new_langflow_content = (
                    langflow_content[:start_idx] +
                    new_chain +
                    langflow_content[end_idx:]
                )
        
        langflow_path.write_text(new_langflow_content)
        print(f"[SAVE] Updated langflow_client.py")
        
        # Success! Close the edit mode and show success message with re-evaluate button
        print(f"[SAVE] ✅ Successfully saved persona: {persona_id}")
        success_toast = html.Div([
            html.Span(f"✅ Saved {new_name} successfully!  ", style={"marginRight": "12px"}),
            html.Button(
                "🔄 Re-evaluate Audio",
                id="re-evaluate-btn",
                n_clicks=0,
                style={
                    "padding": "6px 12px",
                    "backgroundColor": "#ffffff",
                    "color": "#10b981",
                    "border": "1px solid #10b981",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                    "fontSize": "12px",
                    "fontWeight": "500"
                }
            )
        ], style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "backgroundColor": "#10b981",
            "color": "white",
            "padding": "12px 20px",
            "borderRadius": "6px",
            "fontSize": "14px",
            "fontWeight": "500",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
            "zIndex": "10000",
            "display": "flex",
            "alignItems": "center"
        })
        return None, success_toast, {"display": "block"}  # Close form + show toast
        
    except Exception as e:
        print(f"[SAVE] ❌ Error saving persona: {str(e)}")
        import traceback
        traceback.print_exc()
        error_toast = html.Div(f"❌ Error: {str(e)}", style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "backgroundColor": "#ef4444",
            "color": "white",
            "padding": "12px 20px",
            "borderRadius": "6px",
            "fontSize": "14px",
            "fontWeight": "500",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
            "zIndex": "10000",
            "display": "block"
        })
        return dash.no_update, error_toast, {"display": "block"}


# Callback 9: Handle re-evaluation button click
@app.callback(
    Output('save-toast', 'children', allow_duplicate=True),
    Output('save-toast', 'style', allow_duplicate=True),
    Output('segments-store', 'data', allow_duplicate=True),
    Input('re-evaluate-btn', 'n_clicks'),
    State('current-audio-id', 'data'),
    prevent_initial_call=True
)
def trigger_re_evaluation(n_clicks, audio_id):
    """Trigger re-evaluation of current audio file with all personas."""
    import requests
    import time
    
    if not n_clicks or not audio_id:
        raise PreventUpdate
    
    print(f"[RE-EVAL] Triggering re-evaluation for audio: {audio_id}")
    
    try:
        # Show loading toast
        loading_toast = html.Div("🔄 Re-evaluating audio with updated persona settings...", style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "backgroundColor": "#3b82f6",
            "color": "white",
            "padding": "12px 20px",
            "borderRadius": "6px",
            "fontSize": "14px",
            "fontWeight": "500",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
            "zIndex": "10000",
            "display": "block"
        })
        
        # Call backend re-evaluation endpoint
        response = requests.post(f"http://localhost:8000/re-evaluate/{audio_id}")
        response.raise_for_status()
        
        result = response.json()
        print(f"[RE-EVAL] API Response: {result.get('message')}")
        print(f"[RE-EVAL] Queued {result.get('personas_queued')} persona(s)")
        
        # Wait a few seconds for processing (simple polling approach)
        time.sleep(8)
        
        # Fetch updated segments
        segments_response = requests.get(f"http://localhost:8000/segments/{audio_id}")
        segments_response.raise_for_status()
        updated_segments = segments_response.json()
        
        print(f"[RE-EVAL] ✅ Re-evaluation complete, loaded {len(updated_segments)} segments")
        
        # Show success toast
        success_toast = html.Div("✅ Re-evaluation complete! Dashboard updated with new results.", style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "backgroundColor": "#10b981",
            "color": "white",
            "padding": "12px 20px",
            "borderRadius": "6px",
            "fontSize": "14px",
            "fontWeight": "500",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
            "zIndex": "10000",
            "display": "block"
        })
        
        return success_toast, {"display": "block"}, updated_segments
        
    except Exception as e:
        print(f"[RE-EVAL] ❌ Error during re-evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_toast = html.Div(f"❌ Re-evaluation failed: {str(e)}", style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "backgroundColor": "#ef4444",
            "color": "white",
            "padding": "12px 20px",
            "borderRadius": "6px",
            "fontSize": "14px",
            "fontWeight": "500",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)",
            "zIndex": "10000",
            "display": "block"
        })
        return error_toast, {"display": "block"}, dash.no_update


# Callback 1b: Update selected audio store when file button clicked
# Generate inputs dynamically based on actual number of files
audio_files_for_callback = get_all_audio_files()
num_files = len(audio_files_for_callback)

@app.callback(
    Output('selected-audio-store', 'data'),
    [Input(f'file-btn-{i}', 'n_clicks') for i in range(num_files)] if num_files > 0 else [Input('selected-audio-store', 'data')],
    prevent_initial_call=True
)
def update_selected_audio(*n_clicks_list):
    """Update which audio file is selected based on button clicks."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    # Find which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Get the audio_id from the button in the layout
    audio_files = get_all_audio_files()
    if button_id.startswith('file-btn-'):
        index = int(button_id.split('-')[-1])
        if index < len(audio_files):
            selected_id = audio_files[index]['audio_id']
            print(f"[FILE_CLICK] User selected: {selected_id[:16]}...")
            return selected_id
    
    raise PreventUpdate


# Callback 2: Handle file selection and load data
@app.callback(
    Output('current-audio-id', 'data'),
    Output('segments-store', 'data'),
    Output('waveform-data-store', 'data'),
    Output('audio-player-container', 'children'),
    Output('waveform-graph', 'figure', allow_duplicate=True),
    Output('dashboard-audio-id-display', 'children'),
    Output('segment-metadata', 'children', allow_duplicate=True),
    Input('selected-audio-store', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_audio_file(audio_id):
    import numpy as np
    
    print(f"[LOAD_AUDIO] Loading audio_id: {audio_id}")
    
    # If no audio selected, use default
    if not audio_id:
        audio_id = default_audio_id
    
    # If still no audio_id, return empty state
    if not audio_id:
        return (
            None,
            [],
            {'time': [], 'amplitude': [], 'amp_min': 0, 'amp_max': 0},
            html.Div("Select an audio file to begin", style={"padding": "20px", "color": "#6b7280", "textAlign": "center"}),
            {},
            "Select a file",
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
    
    # Cache min/max for performance (avoid recalculating on every update)
    amp_min = float(amplitude.min())
    amp_max = float(amplitude.max())
    
    # Fetch segments
    segments = fetch_segments(audio_id)
    print(f"Loaded {len(segments)} segments")
    
    # Create audio player
    player = render_audio_player(audio_id)
    
    # Create initial waveform
    fig = render_waveform_with_highlight(time, amplitude, segments, amp_min=amp_min, amp_max=amp_max)
    
    # Display text - cleaner format for minimal header
    # Truncate to 12 chars for compact display
    display_text = f"{audio_id[:12]}..." if len(audio_id) > 12 else audio_id
    
    # Initial metadata (first segment)
    if segments and len(segments) > 0:
        metadata = render_metadata_panel(segments[0])
    else:
        metadata = html.Div("No segments available", style={"padding": "20px", "color": "#6b7280"})
    
    return (
        audio_id,
        segments,
        {
            'time': time.tolist(),
            'amplitude': amplitude.tolist(),
            'amp_min': amp_min,
            'amp_max': amp_max
        },
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
            const currentTime = audioElement.currentTime;
            
            // Initialize if needed
            if (window.lastAudioTime === undefined) {
                window.lastAudioTime = currentTime;
            }
            
            // Only update if time has actually changed
            if (Math.abs(currentTime - window.lastAudioTime) >= 0.1) {
                console.log('[CLIENTSIDE] Audio time changed:', window.lastAudioTime, '->', currentTime);
                window.lastAudioTime = currentTime;
                return currentTime;
            }
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
        
        const clicked_time = click_data.points[0].x;
        const audioElement = document.getElementById('audio-player');
        if (audioElement) {
            console.log('[CLIENTSIDE] Seeking to:', clicked_time);
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
    
    print(f"[AUTO_UPDATE] time={current_time}, user_clicked={user_clicked}, has_segments={bool(segments)}, has_waveform={bool(waveform_data)}")
    
    # If user just clicked, reset flag and don't update
    if user_clicked:
        print("[AUTO_UPDATE] User clicked, skipping update")
        return dash.no_update, dash.no_update, False
    
    # Skip if no valid time or segments
    if current_time is None or current_time < 0:
        print(f"[AUTO_UPDATE] Invalid time: {current_time}")
        return dash.no_update, dash.no_update, False
        
    if not segments:
        print("[AUTO_UPDATE] No segments")
        return dash.no_update, dash.no_update, False
        
    if not waveform_data or not waveform_data.get('time'):
        print(f"[AUTO_UPDATE] No waveform data or time: {waveform_data.keys() if waveform_data else 'None'}")
        return dash.no_update, dash.no_update, False
    
    # Convert waveform data back to numpy arrays
    time = np.array(waveform_data['time'])
    amplitude = np.array(waveform_data['amplitude'])
    
    # Get cached min/max (performance optimization)
    amp_min = waveform_data.get('amp_min')
    amp_max = waveform_data.get('amp_max')
    
    # Fallback to calculation if not cached
    if amp_min is None or amp_max is None:
        print("[AUTO_UPDATE] Min/max not cached, calculating...")
        amp_min = float(amplitude.min())
        amp_max = float(amplitude.max())
    
    print(f"[AUTO_UPDATE] Rendering waveform at time {current_time:.2f}, amp_min={amp_min:.3f}, amp_max={amp_max:.3f}")
    
    # Find active segment
    active_segment = next(
        (seg for seg in segments if seg["start"] <= current_time <= seg["end"]),
        None
    )
    
    if active_segment:
        print(f"[AUTO_UPDATE] Active segment: {active_segment.get('start')}-{active_segment.get('end')}")
    
    # Update waveform with cursor (pass cached min/max for performance)
    fig = render_waveform_with_highlight(time, amplitude, segments, cursor_position=current_time, amp_min=amp_min, amp_max=amp_max)
    
    # Update metadata - always render to force UI update
    if active_segment:
        metadata = render_metadata_panel(active_segment)
    else:
        metadata = html.Div(
            "No segment at this time position.",
            style={"padding": "20px", "color": "#6b7280"}
        )
    
    return fig, metadata, False


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


# ============================================================================
# PHASE 3 CALLBACKS: Collapsible Summary Panel on Main Dashboard
# ============================================================================

# Callback 6.1: Fetch summary data when audio changes (Phase 3)
@app.callback(
    Output('summary-data-store', 'data'),
    Input('current-audio-id', 'data'),
    prevent_initial_call=True
)
def fetch_summary_data(audio_id):
    """Fetch summary when audio changes."""
    import requests
    
    if not audio_id:
        return None
    
    try:
        response = requests.get(f"http://localhost:8000/summary/{audio_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching summary for {audio_id}: {e}")
    
    return None


# Callback 6.2: Update summary panel when data is available (Phase 3)
@app.callback(
    Output('summary-panel-container', 'children'),
    Input('summary-data-store', 'data'),
    State('summary-collapsed', 'data'),
    prevent_initial_call=True
)
def update_summary_panel(summary_data, is_collapsed):
    """Render collapsible summary panel on main dashboard."""
    personas = get_all_personas()
    
    if not summary_data:
        return html.Div(
            "Summary loading...",
            style={"padding": "16px", "color": "#6b7280", "fontStyle": "italic"}
        )
    
    # Use the summary_panel component to render
    return render_collapsible_summary(personas, summary_data, is_expanded=not is_collapsed)


# Callback 6.3: Toggle summary collapse state (Phase 3) - SIMPLIFIED
# Only update the collapse state store. The panel re-render is handled by update_summary_panel.
@app.callback(
    Output('summary-collapsed', 'data'),
    Output('summary-panel-container', 'children', allow_duplicate=True),
    Input('summary-collapse-toggle', 'n_clicks'),
    State('summary-collapsed', 'data'),
    State('summary-data-store', 'data'),
    prevent_initial_call=True
)
def toggle_summary_collapse(n_clicks, is_collapsed, summary_data):
    """Toggle the collapse state and re-render the summary panel."""
    if summary_data is None:
        raise PreventUpdate
    
    # Toggle state
    new_collapsed = not is_collapsed
    
    # Re-render the entire panel with new state
    personas = get_all_personas()
    new_panel = render_collapsible_summary(personas, summary_data, is_expanded=not new_collapsed)
    
    return new_collapsed, new_panel


# ============================================================================
# PHASE 4 CALLBACK: Summary Tab
# ============================================================================

# Callback 7: Populate Summary Tab (Phase 4)
@app.callback(
    Output("summary-content", "children"),
    Input("summary-data-store", "data"),
    prevent_initial_call=False
)
def update_summary_tab(summary_data):
    """Generate summary statistics visualization for Summary Tab."""
    personas = get_all_personas()
    
    if not summary_data:
        return html.Div(
            "Select an audio file to view summary",
            style={"padding": "40px", "color": "#6b7280", "textAlign": "center", "fontSize": "16px"}
        )
    
    # Use the summary_panel component to render detailed summary
    return render_detailed_summary(personas, summary_data)


if __name__ == "__main__":
    print(f"\n🚀 Starting dashboard server...")
    print(f"📊 Dashboard available at: http://0.0.0.0:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
