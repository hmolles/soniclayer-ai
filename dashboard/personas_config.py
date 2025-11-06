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
        "display_name": "Business Owner",
        "emoji": "\ud83e\uddd1",
        "description": "Male business owner"
    },
    {
        "id": "stay_at_home_mum",
        "display_name": "Stay At Home Mum",
        "emoji": "\u26bd\ufe0f",
        "description": "Stay at home Mum"
    },
    {
        "id": "tradies",
        "display_name": "Tradies",
        "emoji": "\ud83d\ude0e",
        "description": "Tradies"
    }
]

def get_all_personas():
    """Get all persona configurations"""
    return PERSONAS
