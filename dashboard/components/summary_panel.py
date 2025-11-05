"""
Summary Panel Component - Reusable components for rendering summary data.

This module provides functions for rendering persona summaries in different contexts:
- Collapsible panel on main dashboard (Phase 3)
- Detailed summary tab view (Phase 4)
"""

from dash import html, dcc
import plotly.graph_objects as go


def get_score_color(score: float) -> str:
    """
    Return color hex code based on score (1-5 scale).
    
    Args:
        score: Numeric score between 1.0 and 5.0
        
    Returns:
        Hex color code as string
    """
    if score >= 4.0:
        return "#10b981"  # Green - Excellent
    elif score >= 3.0:
        return "#3b82f6"  # Blue - Good
    elif score >= 2.0:
        return "#f59e0b"  # Orange - Moderate
    else:
        return "#ef4444"  # Red - Low


def create_distribution_bar(score_distribution: dict, height: int = 200) -> go.Figure:
    """
    Create a horizontal bar chart for score distribution.
    
    Args:
        score_distribution: Dict mapping score (1-5) to count
                           Example: {"1": 2, "2": 5, "3": 8, "4": 3, "5": 0}
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    scores = ["1★", "2★", "3★", "4★", "5★"]
    counts = [score_distribution.get(str(i), 0) for i in range(1, 6)]
    colors = [get_score_color(i) for i in range(1, 6)]
    
    fig = go.Figure(data=[
        go.Bar(
            x=scores,
            y=counts,
            marker_color=colors,
            text=counts,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=None,
        xaxis_title="Score",
        yaxis_title="Count",
        height=height,
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#e5e7eb')
    )
    
    return fig


def render_persona_summary_card(persona: dict, stats: dict, compact: bool = False) -> html.Div:
    """
    Render a single persona's summary as a card.
    
    Args:
        persona: Persona config dict with id, display_name, emoji, description
        stats: Summary stats from backend with avg_score, avg_confidence, score_distribution, etc.
        compact: If True, render smaller version for collapsible panel
        
    Returns:
        Dash Div component containing the persona card
    """
    avg_score = stats.get("avg_score", 0)
    avg_confidence = stats.get("avg_confidence", 0)
    score_dist = stats.get("score_distribution", {})
    top_segments = stats.get("top_segments", [])
    worst_segments = stats.get("worst_segments", [])
    
    if compact:
        # Compact version for collapsible panel - card-style with larger score
        return html.Div([
            # Emoji at top
            html.Div(
                persona["emoji"],
                style={
                    "fontSize": "32px",
                    "textAlign": "center",
                    "marginBottom": "8px"
                }
            ),
            
            # Persona name
            html.Div(
                persona["display_name"],
                style={
                    "fontSize": "13px",
                    "fontWeight": "600",
                    "color": "#111827",
                    "textAlign": "center",
                    "marginBottom": "12px"
                }
            ),
            
            # Large score display
            html.Div([
                html.Span(f"{avg_score:.1f}", style={
                    "fontSize": "36px",
                    "fontWeight": "700",
                    "color": get_score_color(avg_score),
                    "lineHeight": "1"
                }),
                html.Span("/5.0", style={
                    "fontSize": "14px",
                    "color": "#9ca3af",
                    "marginLeft": "4px"
                })
            ], style={
                "textAlign": "center",
                "marginBottom": "12px"
            }),
            
            # Confidence bar
            html.Div([
                html.Div(style={
                    "width": "100%",
                    "height": "4px",
                    "backgroundColor": "#e5e7eb",
                    "borderRadius": "2px",
                    "overflow": "hidden"
                }, children=[
                    html.Div(style={
                        "width": f"{avg_confidence * 100}%",
                        "height": "100%",
                        "backgroundColor": get_score_color(avg_score),
                        "borderRadius": "2px",
                        "transition": "width 0.5s ease"
                    })
                ]),
                html.Div(f"{avg_confidence*100:.0f}% confidence", style={
                    "fontSize": "10px",
                    "color": "#6b7280",
                    "marginTop": "6px",
                    "textAlign": "center"
                })
            ])
            
        ], style={
            "padding": "16px",
            "backgroundColor": "#ffffff",
            "borderRadius": "8px",
            "border": f"2px solid {get_score_color(avg_score)}",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.06)",
            "transition": "transform 0.2s ease, box-shadow 0.2s ease",
            "textAlign": "center"
        })
    else:
        # Full version for detailed summary tab
        return html.Div([
            # Card header
            html.Div([
                html.Span(persona["emoji"], style={"fontSize": "32px", "marginRight": "12px"}),
                html.Div([
                    html.H3(persona["display_name"], style={
                        "margin": "0",
                        "fontSize": "18px",
                        "color": "#111827"
                    }),
                    html.P(persona["description"], style={
                        "margin": "4px 0 0 0",
                        "fontSize": "13px",
                        "color": "#6b7280"
                    })
                ], style={"flex": "1"})
            ], style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "16px",
                "paddingBottom": "16px",
                "borderBottom": "2px solid #e5e7eb"
            }),
            
            # Metrics row
            html.Div([
                # Average score
                html.Div([
                    html.Div("Average Score", style={
                        "fontSize": "12px",
                        "color": "#6b7280",
                        "marginBottom": "4px"
                    }),
                    html.Div(f"{avg_score:.1f} / 5.0", style={
                        "fontSize": "24px",
                        "fontWeight": "700",
                        "color": get_score_color(avg_score)
                    })
                ], style={
                    "flex": "1",
                    "padding": "12px",
                    "backgroundColor": "#f9fafb",
                    "borderRadius": "6px",
                    "marginRight": "8px"
                }),
                
                # Confidence
                html.Div([
                    html.Div("Confidence", style={
                        "fontSize": "12px",
                        "color": "#6b7280",
                        "marginBottom": "4px"
                    }),
                    html.Div(f"{avg_confidence*100:.0f}%", style={
                        "fontSize": "24px",
                        "fontWeight": "700",
                        "color": "#3b82f6"
                    })
                ], style={
                    "flex": "1",
                    "padding": "12px",
                    "backgroundColor": "#f9fafb",
                    "borderRadius": "6px"
                })
            ], style={
                "display": "flex",
                "marginBottom": "16px"
            }),
            
            # Score distribution chart
            html.Div([
                html.H4("Score Distribution", style={
                    "margin": "0 0 8px 0",
                    "fontSize": "14px",
                    "color": "#111827"
                }),
                dcc.Graph(figure=create_distribution_bar(score_dist), config={'displayModeBar': False})
            ], style={"marginBottom": "16px"}),
            
            # Top & Worst segments
            html.Div([
                # Top segments
                html.Div([
                    html.H4("🏆 Top Segments", style={
                        "margin": "0 0 8px 0",
                        "fontSize": "14px",
                        "color": "#10b981"
                    }),
                    html.Div([
                        html.Span(f"#{seg}", style={
                            "display": "inline-block",
                            "padding": "4px 8px",
                            "marginRight": "4px",
                            "marginBottom": "4px",
                            "backgroundColor": "#10b98120",
                            "color": "#10b981",
                            "borderRadius": "4px",
                            "fontSize": "12px",
                            "fontWeight": "600"
                        }) for seg in top_segments
                    ])
                ], style={
                    "flex": "1",
                    "marginRight": "8px",
                    "padding": "12px",
                    "backgroundColor": "#f0fdf4",
                    "borderRadius": "6px",
                    "border": "1px solid #10b98140"
                }),
                
                # Worst segments
                html.Div([
                    html.H4("⚠️ Worst Segments", style={
                        "margin": "0 0 8px 0",
                        "fontSize": "14px",
                        "color": "#ef4444"
                    }),
                    html.Div([
                        html.Span(f"#{seg}", style={
                            "display": "inline-block",
                            "padding": "4px 8px",
                            "marginRight": "4px",
                            "marginBottom": "4px",
                            "backgroundColor": "#ef444420",
                            "color": "#ef4444",
                            "borderRadius": "4px",
                            "fontSize": "12px",
                            "fontWeight": "600"
                        }) for seg in worst_segments
                    ])
                ], style={
                    "flex": "1",
                    "padding": "12px",
                    "backgroundColor": "#fef2f2",
                    "borderRadius": "6px",
                    "border": "1px solid #ef444440"
                })
            ], style={
                "display": "flex"
            })
            
        ], style={
            "backgroundColor": "#ffffff",
            "borderRadius": "8px",
            "padding": "20px",
            "marginBottom": "16px",
            "border": "1px solid #e5e7eb",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
        })


def render_collapsible_summary(personas: list, summary_data: dict, is_expanded: bool = True) -> html.Div:
    """
    Render collapsible summary panel for main dashboard (Phase 3).
    
    Args:
        personas: List of persona config dicts
        summary_data: Full summary data from /summary/{audio_id} endpoint
        is_expanded: Whether panel starts expanded
        
    Returns:
        Dash Div component containing the collapsible panel
    """
    if not summary_data or "personas" not in summary_data:
        return html.Div(
            "Summary data not available",
            style={"padding": "16px", "color": "#6b7280", "fontStyle": "italic"}
        )
    
    personas_data = summary_data.get("personas", {})
    num_segments = summary_data.get("num_segments", 0)
    
    # Create compact persona cards
    persona_cards = []
    for persona in personas:
        persona_id = persona["id"]
        if persona_id in personas_data:
            stats = personas_data[persona_id]
            card = render_persona_summary_card(persona, stats, compact=True)
            persona_cards.append(card)
    
    return html.Div([
        # Toggle button
        html.Button([
            html.Span("▼" if is_expanded else "▶", style={"marginRight": "8px"}),
            html.Span(f"📊 Summary ({num_segments} segments)", style={"fontWeight": "600"})
        ], 
        id="summary-collapse-toggle",
        n_clicks=0,
        style={
            "width": "100%",
            "padding": "12px 16px",
            "backgroundColor": "#f3f4f6",
            "border": "none",
            "borderRadius": "8px 8px 0 0" if is_expanded else "8px",
            "cursor": "pointer",
            "fontSize": "14px",
            "color": "#111827",
            "textAlign": "left",
            "transition": "background-color 0.2s",
        }),
        
        # Collapsible content
        html.Div(
            persona_cards,
            id="summary-collapse-content",
            style={
                "padding": "16px",
                "backgroundColor": "#ffffff",
                "borderRadius": "0 0 8px 8px",
                "border": "1px solid #e5e7eb",
                "borderTop": "none",
                "display": "grid" if is_expanded else "none",
                "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))",
                "gap": "12px"
            }
        )
    ], style={
        "marginBottom": "16px"
    })


def render_detailed_summary(personas: list, summary_data: dict) -> html.Div:
    """
    Render detailed summary view for Summary Tab (Phase 4).
    
    Args:
        personas: List of persona config dicts
        summary_data: Full summary data from /summary/{audio_id} endpoint
        
    Returns:
        Dash Div component containing the detailed summary
    """
    if not summary_data or "personas" not in summary_data:
        return html.Div(
            "Select an audio file to view summary",
            style={"padding": "40px", "color": "#6b7280", "textAlign": "center", "fontSize": "16px"}
        )
    
    personas_data = summary_data.get("personas", {})
    num_segments = summary_data.get("num_segments", 0)
    audio_id = summary_data.get("audio_id", "Unknown")
    
    # Create full persona cards
    persona_cards = []
    for persona in personas:
        persona_id = persona["id"]
        if persona_id in personas_data:
            stats = personas_data[persona_id]
            card = render_persona_summary_card(persona, stats, compact=False)
            persona_cards.append(card)
    
    # Header with overview
    header = html.Div([
        html.H2(f"📊 Summary for Audio: {audio_id[:16]}...", style={
            "margin": "0 0 8px 0",
            "fontSize": "24px",
            "color": "#111827"
        }),
        html.P(f"Total Segments: {num_segments}", style={
            "margin": "0",
            "fontSize": "14px",
            "color": "#6b7280"
        })
    ], style={
        "marginBottom": "24px",
        "paddingBottom": "16px",
        "borderBottom": "2px solid #e5e7eb"
    })
    
    return html.Div([header] + persona_cards)
