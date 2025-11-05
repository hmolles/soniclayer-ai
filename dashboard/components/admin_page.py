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
                        ),
                        html.Div(
                            id="json-validation-message",
                            style={"marginTop": "8px", "fontSize": "12px"}
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
                
                html.Div([
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
                                html.Span(f"ID: {persona['id']}", style={
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
                            ])
                        ], style={
                            "display": "flex",
                            "alignItems": "flex-start"
                        })
                    ], style={
                        "padding": "16px",
                        "backgroundColor": "#f9fafb",
                        "border": "1px solid #e5e7eb",
                        "borderRadius": "6px",
                        "marginBottom": "12px"
                    }) for persona in personas
                ], id="personas-list")
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
