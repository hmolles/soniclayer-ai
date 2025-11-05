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


def create_distribution_bar(score_distribution: dict, height: int = 120) -> go.Figure:
    """
    Create a minimal horizontal bar chart for score distribution.
    
    Args:
        score_distribution: Dict mapping score (1-5) to count
                           Example: {"1": 2, "2": 5, "3": 8, "4": 3, "5": 0}
        height: Chart height in pixels (default: 120 for compact design)
        
    Returns:
        Plotly figure object
    """
    scores = ["1★", "2★", "3★", "4★", "5★"]
    counts = [score_distribution.get(str(i), 0) for i in range(1, 6)]
    
    # Monochromatic slate colors - minimal design
    colors = ['#cbd5e1', '#cbd5e1', '#94a3b8', '#64748b', '#0f172a']
    
    fig = go.Figure(data=[
        go.Bar(
            x=scores,
            y=counts,
            marker_color=colors,
            text=counts,
            textposition='outside',
            textfont=dict(size=11, color='#64748b')
        )
    ])
    
    fig.update_layout(
        title=None,
        xaxis_title=None,
        yaxis_title=None,
        height=height,
        margin=dict(l=20, r=20, t=10, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=False, showline=False, showticklabels=False),
        font=dict(size=11, color='#64748b')
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
        # Extra compact version for always-visible panel
        return html.Div([
            # Emoji and name inline
            html.Div([
                html.Span(persona["emoji"], style={
                    "fontSize": "20px",
                    "marginRight": "6px"
                }),
                html.Span(persona["display_name"], style={
                    "fontSize": "12px",
                    "fontWeight": "500",
                    "color": "#0f172a"
                })
            ], style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "6px"
            }),
            
            # Score and confidence inline
            html.Div([
                html.Span(f"{avg_score:.1f}", style={
                    "fontSize": "20px",
                    "fontWeight": "700",
                    "color": get_score_color(avg_score),
                    "marginRight": "4px"
                }),
                html.Span(f"({avg_confidence*100:.0f}%)", style={
                    "fontSize": "11px",
                    "color": "#94a3b8"
                })
            ], style={
                "display": "flex",
                "alignItems": "baseline"
            })
            
        ], style={
            "padding": "8px 12px",
            "backgroundColor": "#fafafa",
            "borderRadius": "4px",
            "border": f"1px solid {get_score_color(avg_score)}",
            "borderLeftWidth": "3px",
            "minWidth": "140px"
        })
    else:
        # Full version for detailed summary tab - MINIMAL DESIGN
        return html.Div([
            # Minimal header with persona info
            html.Div([
                html.Span(persona["emoji"], style={
                    "fontSize": "20px",
                    "marginRight": "10px"
                }),
                html.Div([
                    html.H3(persona["display_name"], style={
                        "margin": "0",
                        "fontSize": "15px",
                        "fontWeight": "500",
                        "color": "#0f172a"
                    }),
                    html.P(persona["description"], style={
                        "margin": "2px 0 0 0",
                        "fontSize": "12px",
                        "color": "#94a3b8"
                    })
                ], style={"flex": "1"})
            ], style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "16px",
                "paddingBottom": "12px",
                "borderBottom": "1px solid #f1f5f9"
            }),
            
            # Compact metrics row
            html.Div([
                # Average score
                html.Div([
                    html.Div("Avg Score", style={
                        "fontSize": "11px",
                        "color": "#94a3b8",
                        "marginBottom": "4px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.05em"
                    }),
                    html.Div(f"{avg_score:.1f}", style={
                        "fontSize": "28px",
                        "fontWeight": "500",
                        "color": "#0f172a",
                        "lineHeight": "1"
                    }),
                    html.Div("/ 5.0", style={
                        "fontSize": "12px",
                        "color": "#cbd5e1",
                        "marginTop": "2px"
                    })
                ], style={
                    "flex": "1",
                    "marginRight": "12px"
                }),
                
                # Confidence
                html.Div([
                    html.Div("Confidence", style={
                        "fontSize": "11px",
                        "color": "#94a3b8",
                        "marginBottom": "4px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.05em"
                    }),
                    html.Div(f"{avg_confidence*100:.0f}%", style={
                        "fontSize": "28px",
                        "fontWeight": "500",
                        "color": "#0f172a",
                        "lineHeight": "1"
                    })
                ], style={
                    "flex": "1"
                })
            ], style={
                "display": "flex",
                "marginBottom": "16px"
            }),
            
            # Compact score distribution chart
            html.Div([
                html.Div("Score Distribution", style={
                    "fontSize": "11px",
                    "color": "#94a3b8",
                    "marginBottom": "8px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em"
                }),
                dcc.Graph(
                    figure=create_distribution_bar(score_dist, height=120),
                    config={'displayModeBar': False},
                    style={"margin": "0 -12px"}
                )
            ], style={"marginBottom": "16px"}),
            
            # Minimal top & worst segments
            html.Div([
                # Top segments
                html.Div([
                    html.Div("Top Segments", style={
                        "fontSize": "11px",
                        "color": "#94a3b8",
                        "marginBottom": "6px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.05em"
                    }),
                    html.Div([
                        html.Span(f"#{seg}", style={
                            "display": "inline-block",
                            "padding": "3px 8px",
                            "marginRight": "4px",
                            "marginBottom": "4px",
                            "backgroundColor": "#f8fafc",
                            "color": "#64748b",
                            "fontSize": "11px",
                            "fontWeight": "500",
                            "border": "1px solid #f1f5f9"
                        }) for seg in top_segments
                    ])
                ], style={
                    "flex": "1",
                    "marginRight": "12px"
                }),
                
                # Worst segments
                html.Div([
                    html.Div("Worst Segments", style={
                        "fontSize": "11px",
                        "color": "#94a3b8",
                        "marginBottom": "6px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.05em"
                    }),
                    html.Div([
                        html.Span(f"#{seg}", style={
                            "display": "inline-block",
                            "padding": "3px 8px",
                            "marginRight": "4px",
                            "marginBottom": "4px",
                            "backgroundColor": "#f8fafc",
                            "color": "#64748b",
                            "fontSize": "11px",
                            "fontWeight": "500",
                            "border": "1px solid #f1f5f9"
                        }) for seg in worst_segments
                    ])
                ], style={
                    "flex": "1"
                })
            ], style={
                "display": "flex"
            })
            
        ], style={
            "backgroundColor": "#ffffff",
            "borderRadius": "0",
            "padding": "20px",
            "marginBottom": "12px",
            "border": "1px solid #f1f5f9",
            "boxShadow": "none"
        })


def render_collapsible_summary(personas: list, summary_data: dict, is_expanded: bool = True) -> html.Div:
    """
    Render summary panel for main dashboard (Phase 3) - always visible, compact design.
    
    Args:
        personas: List of persona config dicts
        summary_data: Full summary data from /summary/{audio_id} endpoint
        is_expanded: Ignored - panel is always visible now
        
    Returns:
        Dash Div component containing the summary panel
    """
    if not summary_data or "personas" not in summary_data:
        return html.Div(
            "Summary data not available",
            style={"padding": "12px", "color": "#6b7280", "fontStyle": "italic", "fontSize": "13px"}
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
        # Simple header (no toggle button)
        html.Div([
            html.Span(f"📊 Summary ({num_segments} segments)", style={
                "fontWeight": "500",
                "fontSize": "13px",
                "color": "#0f172a"
            })
        ], style={
            "padding": "8px 12px",
            "backgroundColor": "#fafafa",
            "borderRadius": "6px 6px 0 0",
            "borderBottom": "1px solid #e5e7eb"
        }),
        
        # Always-visible content
        html.Div(
            persona_cards,
            style={
                "padding": "12px",
                "backgroundColor": "#ffffff",
                "borderRadius": "0 0 6px 6px",
                "border": "1px solid #e5e7eb",
                "borderTop": "none",
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "8px"
            }
        )
    ], style={
        "marginBottom": "0",
        "marginTop": "12px"
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
    
    # Minimal header with overview
    header = html.Div([
        html.Div(f"Summary for Audio: {audio_id[:20]}...", style={
            "margin": "0 0 4px 0",
            "fontSize": "13px",
            "color": "#94a3b8",
            "textTransform": "uppercase",
            "letterSpacing": "0.05em"
        }),
        html.Div(f"Total Segments: {num_segments}", style={
            "margin": "0",
            "fontSize": "15px",
            "fontWeight": "500",
            "color": "#0f172a"
        })
    ], style={
        "marginBottom": "24px",
        "paddingBottom": "16px",
        "borderBottom": "1px solid #f1f5f9"
    })
    
    # Use grid layout for better information density
    return html.Div([
        header,
        html.Div(persona_cards, style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(400px, 1fr))",
            "gap": "16px"
        })
    ])
