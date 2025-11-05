from app.models.personas.persona_agent import PersonaAgent


class GenZAgent(PersonaAgent):
    """
    Gen Z Persona Agent - Represents young adults aged 18-25.
    
    Preferences:
    - Prefers humorous, excited, and casual tones
    - Interested in pop culture, technology, entertainment
    - Dislikes formal, overly serious content
    - Sensitive to repetitive content
    """
    
    def __init__(self):
        name = "GenZ"
        description = "a Gen Z listener aged 18-25 who values authenticity, humor, and cultural relevance"
        
        preferences = {
            "preferred_tones": ["humorous", "excited", "casual"],
            "preferred_topics": ["entertainment", "technology", "lifestyle", "food"],
            "disliked_tags": ["repetition", "formal"],
            "disliked_tones": ["formal", "academic"]
        }
        
        rubric = {
            "engagement": 0.4,      # How entertaining/engaging is it?
            "relevance": 0.3,       # Is it culturally relevant to Gen Z?
            "authenticity": 0.2,    # Does it feel genuine?
            "format": 0.1           # Is the delivery style appropriate?
        }
        
        super().__init__(name, description, preferences, rubric)
    
    def score_segment(self, topic: str, tone: str, transcript: str, tags: list) -> int:
        """
        Custom scoring logic for Gen Z preferences.
        Overrides base class to add Gen Z-specific adjustments.
        """
        score = 3  # Start with neutral
        
        # Tone preferences (strong influence)
        if tone.lower() in self.preferences.get("preferred_tones", []):
            score += 1
        if tone.lower() in self.preferences.get("disliked_tones", []):
            score -= 2
        
        # Topic preferences
        if topic.lower() in self.preferences.get("preferred_topics", []):
            score += 1
        
        # Strong negative reaction to formal content
        if tone.lower() == "formal" or "academic" in tone.lower():
            score -= 1
        
        # Penalty for disliked tags
        if any(tag in self.preferences.get("disliked_tags", []) for tag in tags):
            score -= 1
        
        # Extra penalty for repetition (Gen Z has short attention span)
        if "repetition" in tags:
            score -= 1
        
        # Bonus for excited/energetic content
        if tone.lower() == "excited":
            score += 1
        
        return max(1, min(score, 5))
    
    def generate_opinion(self, score: int, topic: str, tone: str) -> str:
        """Generate Gen Z-appropriate opinions."""
        if score >= 4:
            return f"This {topic} segment really hit different - {tone} tone was perfect! 🔥"
        elif score == 3:
            return f"The {topic} content was okay, but the {tone} vibe didn't quite land for me."
        else:
            return f"Not gonna lie, this {topic} segment felt kinda mid. The {tone} approach didn't work."
    
    def generate_note(self, topic: str, tone: str, tags: list) -> str:
        """Generate Gen Z-specific notes."""
        if "repetition" in tags:
            return "We've heard this before - needs fresh content"
        if "profanity" in tags:
            return "Language is fine for Gen Z audience"
        if tone.lower() == "formal":
            return "Too formal - needs more casual energy"
        return ""
