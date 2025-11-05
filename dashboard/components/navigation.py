"""Navigation menu component for dashboard."""
from dash import html, dcc

def render_navigation(current_page="/"):
    """
    Render navigation menu in top-right corner.
    
    Args:
        current_page: Current page path (/files, /dashboard, /admin)
    """
    return html.Div([
        html.Div([
            dcc.Link(
                "📁 Files",
                href="/files",
                style={
                    "padding": "8px 16px",
                    "marginRight": "8px",
                    "borderRadius": "6px",
                    "textDecoration": "none",
                    "color": "#ffffff" if current_page == "/files" else "#374151",
                    "backgroundColor": "#3b82f6" if current_page == "/files" else "transparent",
                    "fontWeight": "500",
                    "fontSize": "14px",
                    "transition": "all 0.2s"
                }
            ),
            dcc.Link(
                "⚙️ Admin",
                href="/admin",
                style={
                    "padding": "8px 16px",
                    "borderRadius": "6px",
                    "textDecoration": "none",
                    "color": "#ffffff" if current_page == "/admin" else "#374151",
                    "backgroundColor": "#3b82f6" if current_page == "/admin" else "transparent",
                    "fontWeight": "500",
                    "fontSize": "14px",
                    "transition": "all 0.2s"
                }
            )
        ], style={
            "display": "flex",
            "gap": "4px"
        })
    ], style={
        "position": "absolute",
        "top": "20px",
        "right": "20px"
    })
