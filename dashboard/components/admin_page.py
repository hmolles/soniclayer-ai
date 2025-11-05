"""Admin page component for managing personas."""
from dash import html, dcc
from personas_config import get_all_personas

def render_admin_page():
    """Render the admin page for persona management."""
    personas = get_all_personas()
    
    return html.Div([
        # Header
        html.Div([
            html.H2("⚙️ Persona Admin Panel", style={
                "margin": "0 0 8px 0",
                "color": "#111827",
                "fontSize": "24px"
            }),
            html.P("Add and manage audience personas for audio analysis", style={
                "margin": "0",
                "color": "#6b7280",
                "fontSize": "14px"
            })
        ], style={
            "marginBottom": "32px"
        }),
        
        # Two columns layout
        html.Div([
            # Left column - Add New Persona Form
            html.Div([
                html.H3("➕ Add New Persona", style={
                    "margin": "0 0 20px 0",
                    "color": "#111827",
                    "fontSize": "18px"
                }),
                
                # Form
                html.Div([
                    # Persona ID
                    html.Div([
                        html.Label("Persona ID *", style={
                            "display": "block",
                            "marginBottom": "6px",
                            "fontWeight": "500",
                            "fontSize": "14px",
                            "color": "#374151"
                        }),
                        dcc.Input(
                            id="persona-id-input",
                            type="text",
                            placeholder="e.g., millennial, boomer, techie",
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "border": "1px solid #d1d5db",
                                "borderRadius": "6px",
                                "fontSize": "14px",
                                "boxSizing": "border-box"
                            }
                        ),
                        html.Small("Lowercase, no spaces (use underscores)", style={
                            "color": "#6b7280",
                            "fontSize": "12px",
                            "marginTop": "4px",
                            "display": "block"
                        })
                    ], style={"marginBottom": "16px"}),
                    
                    # Display Name
                    html.Div([
                        html.Label("Display Name *", style={
                            "display": "block",
                            "marginBottom": "6px",
                            "fontWeight": "500",
                            "fontSize": "14px",
                            "color": "#374151"
                        }),
                        dcc.Input(
                            id="persona-name-input",
                            type="text",
                            placeholder="e.g., Millennial, Baby Boomer, Tech Enthusiast",
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "border": "1px solid #d1d5db",
                                "borderRadius": "6px",
                                "fontSize": "14px",
                                "boxSizing": "border-box"
                            }
                        )
                    ], style={"marginBottom": "16px"}),
                    
                    # Emoji
                    html.Div([
                        html.Label("Emoji", style={
                            "display": "block",
                            "marginBottom": "6px",
                            "fontWeight": "500",
                            "fontSize": "14px",
                            "color": "#374151"
                        }),
                        dcc.Input(
                            id="persona-emoji-input",
                            type="text",
                            placeholder="e.g., 🎯 👴 💻",
                            maxLength=2,
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "border": "1px solid #d1d5db",
                                "borderRadius": "6px",
                                "fontSize": "14px",
                                "boxSizing": "border-box"
                            }
                        )
                    ], style={"marginBottom": "16px"}),
                    
                    # Description
                    html.Div([
                        html.Label("Description", style={
                            "display": "block",
                            "marginBottom": "6px",
                            "fontWeight": "500",
                            "fontSize": "14px",
                            "color": "#374151"
                        }),
                        dcc.Input(
                            id="persona-description-input",
                            type="text",
                            placeholder="Brief description of this persona",
                            style={
                                "width": "100%",
                                "padding": "10px",
                                "border": "1px solid #d1d5db",
                                "borderRadius": "6px",
                                "fontSize": "14px",
                                "boxSizing": "border-box"
                            }
                        )
                    ], style={"marginBottom": "20px"}),
                    
                    # JSON Prompt
                    html.Div([
                        html.Label("Evaluation Prompt (JSON) *", style={
                            "display": "block",
                            "marginBottom": "6px",
                            "fontWeight": "500",
                            "fontSize": "14px",
                            "color": "#374151"
                        }),
                        dcc.Textarea(
                            id="persona-prompt-input",
                            placeholder='{\n  "system": "You are a [persona] evaluator...",\n  "user_template": "Evaluate this segment..."\n}',
                            style={
                                "width": "100%",
                                "height": "200px",
                                "padding": "10px",
                                "border": "1px solid #d1d5db",
                                "borderRadius": "6px",
                                "fontSize": "13px",
                                "fontFamily": "monospace",
                                "boxSizing": "border-box",
                                "resize": "vertical"
                            }
                        )
                    ], style={"marginBottom": "20px"}),
                    
                    # Submit Button
                    html.Button(
                        "Create Persona",
                        id="create-persona-button",
                        n_clicks=0,
                        style={
                            "width": "100%",
                            "padding": "12px",
                            "backgroundColor": "#3b82f6",
                            "color": "white",
                            "border": "none",
                            "borderRadius": "6px",
                            "fontSize": "14px",
                            "fontWeight": "600",
                            "cursor": "pointer",
                            "transition": "background-color 0.2s"
                        }
                    ),
                    
                    # Feedback message
                    html.Div(
                        id="creation-feedback",
                        style={"marginTop": "12px"}
                    )
                ])
            ], style={
                "flex": "1",
                "backgroundColor": "#ffffff",
                "padding": "24px",
                "borderRadius": "8px",
                "border": "1px solid #e5e7eb",
                "marginRight": "20px"
            }),
            
            # Right column - Existing Personas List
            html.Div([
                html.H3("👥 Existing Personas", style={
                    "margin": "0 0 20px 0",
                    "color": "#111827",
                    "fontSize": "18px"
                }),
                
                # Store to track which persona is being edited
                dcc.Store(id="editing-persona-id", data=None),
                
                # Store to track re-evaluation state
                dcc.Store(id="re-evaluate-status", data=None),
                
                # Toast notification for save feedback
                html.Div(id="save-toast", style={"display": "none"}),
                
                # Container for persona cards (will be updated by callback)
                html.Div(id="personas-list")
            ], style={
                "width": "350px",
                "backgroundColor": "#ffffff",
                "padding": "24px",
                "borderRadius": "8px",
                "border": "1px solid #e5e7eb",
                "maxHeight": "600px",
                "overflowY": "auto"
            })
        ], style={
            "display": "flex",
            "marginBottom": "20px"
        })
    ], style={
        "padding": "40px",
        "maxWidth": "1400px",
        "margin": "0 auto"
    })
