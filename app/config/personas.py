"""
Central Persona Registry

This file defines all available personas in the system.
To add a new persona:
1. Create the worker file (app/workers/{persona_id}_worker.py)
2. Add the persona prompt to langflow_client.py
3. Add an entry to PERSONAS list below
4. The system will automatically pick it up!
"""

from typing import List, Dict

# Persona Configuration
PERSONAS: List[Dict[str, str]] = [
    {
        "id": "genz",                                    # Used in Redis keys, worker imports
        "display_name": "Gen Z",                         # Shown in dashboard
        "emoji": "🔥",                                   # Icon for UI
        "worker_module": "app.workers.genz_worker",      # Python import path
        "chain_name": "genz_chain",                      # Langflow chain identifier
        "description": "Gen Z listener aged 18-25"       # Tooltip/description
    },
    {
        "id": "advertiser",
        "display_name": "Advertiser",
        "emoji": "💼",
        "worker_module": "app.workers.advertiser_worker",
        "chain_name": "advertiser_chain",
        "description": "Brand safety evaluator"
    },
    {
        "id": "business_owner",
        "display_name": "Business Owner",
        "emoji": "🥸",
        "worker_module": "app.workers.business_owner_worker",
        "chain_name": "business_owner_chain",
        "description": "Male business owner"
    }
]

# Helper functions
def get_persona_ids() -> List[str]:
    """Get list of all persona IDs"""
    return [p["id"] for p in PERSONAS]

def get_persona_by_id(persona_id: str) -> Dict[str, str]:
    """Get persona config by ID"""
    for persona in PERSONAS:
        if persona["id"] == persona_id:
            return persona
    raise ValueError(f"Persona '{persona_id}' not found in registry")

def get_all_personas() -> List[Dict[str, str]]:
    """Get all persona configurations"""
    return PERSONAS
