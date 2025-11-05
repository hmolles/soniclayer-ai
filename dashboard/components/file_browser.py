"""File browser component for displaying available audio files."""
from dash import html, dcc
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.audio_scanner import get_all_audio_files


def render_file_browser():
    """Render the file browser page showing all available audio files."""
    audio_files = get_all_audio_files()
    
    if not audio_files:
        return html.Div([
            html.Div([
                html.H2("📁 Audio Files", style={
                    "margin": "0 0 8px 0",
                    "color": "#111827",
                    "fontSize": "24px"
                }),
                html.P("No audio files found in uploads folder", style={
                    "margin": "0",
                    "color": "#6b7280",
                    "fontSize": "14px"
                })
            ])
        ], style={"padding": "40px"})
    
    # Create audio file cards
    file_cards = []
    
    for audio in audio_files:
        # Shorten audio_id for display
        short_id = audio["audio_id"][:16] + "..."
        
        card = html.Div([
            # Header with audio icon and ID
            html.Div([
                html.Span("🎵", style={
                    "fontSize": "32px",
                    "marginRight": "12px"
                }),
                html.Div([
                    html.Div(short_id, style={
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "color": "#111827",
                        "marginBottom": "4px"
                    }),
                    html.Div(audio["filename"], style={
                        "fontSize": "12px",
                        "color": "#6b7280",
                        "fontFamily": "monospace"
                    })
                ])
            ], style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "16px"
            }),
            
            # Metadata
            html.Div([
                html.Div([
                    html.Span("📊 Segments: ", style={"color": "#6b7280", "fontSize": "14px"}),
                    html.Span(str(audio["num_segments"]), style={"fontWeight": "600", "fontSize": "14px"})
                ], style={"marginBottom": "8px"}),
                
                html.Div([
                    html.Span("💾 Size: ", style={"color": "#6b7280", "fontSize": "14px"}),
                    html.Span(f"{audio['file_size_mb']} MB", style={"fontWeight": "600", "fontSize": "14px"})
                ], style={"marginBottom": "8px"}),
                
                html.Div([
                    html.Span("📅 Uploaded: ", style={"color": "#6b7280", "fontSize": "14px"}),
                    html.Span(audio["upload_date"], style={"fontWeight": "600", "fontSize": "14px"})
                ])
            ], style={"marginBottom": "16px"}),
            
            # View Dashboard button
            html.A(
                "View Dashboard →",
                href=f"/dashboard?audio_id={audio['audio_id']}",
                style={
                    "display": "inline-block",
                    "padding": "10px 20px",
                    "backgroundColor": "#3b82f6",
                    "color": "white",
                    "textDecoration": "none",
                    "borderRadius": "6px",
                    "fontSize": "14px",
                    "fontWeight": "600",
                    "textAlign": "center",
                    "cursor": "pointer",
                    "transition": "background-color 0.2s"
                }
            )
        ], style={
            "backgroundColor": "#ffffff",
            "padding": "24px",
            "borderRadius": "8px",
            "border": "1px solid #e5e7eb",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
            "marginBottom": "16px"
        })
        
        file_cards.append(card)
    
    return html.Div([
        # Header
        html.Div([
            html.H2("📁 Audio Files", style={
                "margin": "0 0 8px 0",
                "color": "#111827",
                "fontSize": "24px"
            }),
            html.P(f"Found {len(audio_files)} audio file{'s' if len(audio_files) != 1 else ''} in uploads", style={
                "margin": "0",
                "color": "#6b7280",
                "fontSize": "14px"
            })
        ], style={
            "marginBottom": "32px"
        }),
        
        # File cards grid
        html.Div(file_cards, style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fill, minmax(350px, 1fr))",
            "gap": "20px"
        })
    ], style={
        "padding": "40px",
        "maxWidth": "1400px",
        "margin": "0 auto"
    })
