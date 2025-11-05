"""Metadata panel component for displaying segment information."""
from dash import html


def get_score_color(score):
    """Get color based on score (1-5 scale)"""
    if score >= 4:
        return "#10b981"  # Green - success
    elif score == 3:
        return "#f59e0b"  # Amber - neutral
    else:
        return "#ef4444"  # Red - warning


def render_persona_card(persona_name, persona_data, emoji):
    """
    Render a persona evaluation card with score, opinion, and details.
    
    Args:
        persona_name: Display name (e.g., "Gen Z", "Advertiser")
        persona_data: Dict with score, opinion, rationale, confidence, note
        emoji: Emoji to display for this persona
    
    Returns:
        Dash HTML component
    """
    if not persona_data:
        return html.Div(
            [
                html.Div([
                    html.Span(emoji, style={"fontSize": "24px", "marginRight": "8px"}),
                    html.Span(persona_name, style={"fontWeight": "bold", "fontSize": "16px"}),
                ], style={"marginBottom": "8px"}),
                html.Div("⏳ Processing...", style={
                    "fontSize": "14px",
                    "color": "#6b7280",
                    "fontStyle": "italic"
                })
            ],
            style={
                "padding": "16px",
                "marginBottom": "12px",
                "borderRadius": "8px",
                "border": "2px solid #e5e7eb",
                "backgroundColor": "#f9fafb"
            }
        )
    
    score = persona_data.get("score", 0)
    opinion = persona_data.get("opinion", "No opinion")
    rationale = persona_data.get("rationale", "")
    confidence = persona_data.get("confidence", 0)
    note = persona_data.get("note", "")
    
    score_color = get_score_color(score)
    
    return html.Div(
        [
            # Header with emoji, name, and score badge
            html.Div([
                html.Div([
                    html.Span(emoji, style={"fontSize": "24px", "marginRight": "8px"}),
                    html.Span(persona_name, style={"fontWeight": "bold", "fontSize": "16px"}),
                ], style={"display": "inline-block"}),
                html.Div(
                    f"{score}/5",
                    style={
                        "display": "inline-block",
                        "float": "right",
                        "backgroundColor": score_color,
                        "color": "white",
                        "padding": "4px 12px",
                        "borderRadius": "16px",
                        "fontWeight": "bold",
                        "fontSize": "14px"
                    }
                )
            ], style={"marginBottom": "12px"}),
            
            # Opinion
            html.Div([
                html.Strong("💭 Opinion: "),
                html.Span(opinion, style={"color": "#374151"})
            ], style={"marginBottom": "8px", "fontSize": "14px"}),
            
            # Rationale
            html.Div([
                html.Strong("📝 Rationale: "),
                html.Span(rationale, style={"color": "#6b7280", "fontSize": "13px"})
            ], style={"marginBottom": "8px"}),
            
            # Confidence bar
            html.Div([
                html.Strong("🎯 Confidence: ", style={"fontSize": "13px"}),
                html.Div(
                    style={
                        "height": "8px",
                        "backgroundColor": "#e5e7eb",
                        "borderRadius": "4px",
                        "marginTop": "4px",
                        "overflow": "hidden"
                    },
                    children=[
                        html.Div(
                            style={
                                "height": "100%",
                                "width": f"{confidence * 100}%",
                                "backgroundColor": score_color,
                                "transition": "width 0.3s ease"
                            }
                        )
                    ]
                ),
                html.Span(f"{int(confidence * 100)}%", style={
                    "fontSize": "12px",
                    "color": "#6b7280",
                    "marginTop": "2px",
                    "display": "block"
                })
            ], style={"marginBottom": "8px"}),
            
            # Note (if exists)
            html.Div([
                html.Strong("📌 Note: "),
                html.Span(note, style={"color": "#6b7280", "fontSize": "12px", "fontStyle": "italic"})
            ], style={"marginTop": "8px"}) if note and note != "None" else None
        ],
        style={
            "padding": "16px",
            "marginBottom": "12px",
            "borderRadius": "8px",
            "border": f"2px solid {score_color}",
            "backgroundColor": "#ffffff",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
        }
    )


def render_metadata_panel(segment):
    """
    Render metadata panel for a segment with persona evaluations.
    
    Args:
        segment: Dict with keys: topic, tone, transcript, genz, advertiser, note
        
    Returns:
        Dash HTML component or None
    """
    if segment is None:
        return html.Div(
            "🎵 No segment selected - click on the waveform or wait for playback",
            style={
                "padding": "20px",
                "textAlign": "center",
                "color": "#6b7280",
                "fontStyle": "italic"
            }
        )
    
    # Extract data with defaults
    topic = segment.get("topic", "Unknown")
    tone = segment.get("tone", "Unknown")
    transcript = segment.get("transcript", "")
    note = segment.get("note", "")
    genz_data = segment.get("genz")
    advertiser_data = segment.get("advertiser")
    
    # Check if segment is instrumental/music only (very short or empty transcript)
    is_instrumental = len(transcript.strip()) < 20
    if is_instrumental and not note:
        note = "🎵 Instrumental/Music section"
    
    return html.Div([
        # Segment header
        html.Div([
            html.H3("📊 Segment Analysis", style={"marginBottom": "8px", "color": "#111827"}),
            html.Div([
                html.Span("📂 ", style={"marginRight": "4px"}),
                html.Strong("Topic: "),
                html.Span(topic, style={
                    "backgroundColor": "#dbeafe",
                    "padding": "2px 8px",
                    "borderRadius": "4px",
                    "fontSize": "13px",
                    "marginRight": "12px"
                }),
                html.Span("🎭 ", style={"marginRight": "4px"}),
                html.Strong("Tone: "),
                html.Span(tone, style={
                    "backgroundColor": "#fef3c7",
                    "padding": "2px 8px",
                    "borderRadius": "4px",
                    "fontSize": "13px"
                })
            ], style={"marginBottom": "12px"}),
        ], style={"marginBottom": "16px"}),
        
        # Transcript
        html.Div([
            html.Strong("📝 Transcript:", style={"display": "block", "marginBottom": "8px"}),
            html.Div(
                transcript,
                style={
                    "padding": "12px",
                    "backgroundColor": "#f9fafb",
                    "borderRadius": "6px",
                    "fontSize": "14px",
                    "lineHeight": "1.6",
                    "color": "#374151",
                    "border": "1px solid #e5e7eb",
                    "maxHeight": "120px",
                    "overflowY": "auto"
                }
            )
        ], style={"marginBottom": "20px"}),
        
        # Persona evaluations
        html.Div([
            html.H4("🎯 Persona Evaluations", style={"marginBottom": "12px", "color": "#111827"}),
            render_persona_card("🔥 Gen Z", genz_data, "🔥"),
            render_persona_card("💼 Advertiser", advertiser_data, "💼"),
        ]),
        
        # Additional note
        html.Div([
            html.Div(
                [html.Strong("⚠️ "), note],
                style={
                    "padding": "8px 12px",
                    "backgroundColor": "#fef3c7",
                    "borderRadius": "6px",
                    "fontSize": "13px",
                    "border": "1px solid #fbbf24"
                }
            )
        ], style={"marginTop": "12px"}) if note else None
    ], style={
        "padding": "20px",
        "height": "100%",
        "overflowY": "auto"
    })
