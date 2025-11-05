"""
Persona configuration for dashboard.
This mirrors the configuration in app/config/personas.py
"""

PERSONAS = [
    {
        "id": "genz",
        "display_name": "Gen Z",
        "emoji": "🔥",
        "description": "Gen Z listener aged 18-25"
    },
    {
        "id": "advertiser",
        "display_name": "Advertiser",
        "emoji": "💼",
        "description": "Brand safety evaluator"
    }
]

def get_all_personas():
    """Get all persona configurations"""
    return PERSONAS
