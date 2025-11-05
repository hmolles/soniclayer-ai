"""
Persona configuration for dashboard.
This mirrors the configuration in app/config/personas.py
"""

PERSONAS = [
    {
        "id": "genz",
        "display_name": "Gen Z",
        "emoji": "\ud83d\udd25",
        "description": "Gen Z listener aged 18-25"
    },
    {
        "id": "advertiser",
        "display_name": "Advertiser",
        "emoji": "\ud83d\udcbc",
        "description": "Brand safety evaluator"
    },
    {
        "id": "business_owner",
        "display_name": "",
        "emoji": "",
        "description": ""
    }
]

def get_all_personas():
    """Get all persona configurations"""
    return PERSONAS
