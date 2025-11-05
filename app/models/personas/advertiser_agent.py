from app.models.personas.persona_agent import PersonaAgent


class AdvertiserAgent(PersonaAgent):
    """
    Advertiser Persona Agent - Represents commercial sponsors and brand partners.
    
    Preferences:
    - Prefers excited, informative tones that drive engagement
    - Interested in topics with high commercial value
    - Values content that attracts attention and drives action
    - Dislikes controversial or negative content
    """
    
    def __init__(self):
        name = "Advertiser"
        description = "a commercial sponsor evaluating content for brand safety and audience engagement potential"
        
        preferences = {
            "preferred_tones": ["excited", "informative", "positive"],
            "preferred_topics": ["technology", "food", "lifestyle", "health", "entertainment"],
            "disliked_tags": ["profanity", "controversial", "negative"],
            "disliked_tones": ["controversial", "negative", "depressing"]
        }
        
        rubric = {
            "brand_safety": 0.35,       # Is it safe for brand association?
            "engagement_potential": 0.30, # Will it attract audience attention?
            "commercial_value": 0.25,    # Does it relate to purchasable products/services?
            "demographic_reach": 0.10    # Does it appeal to valuable demographics?
        }
        
        super().__init__(name, description, preferences, rubric)
    
    def score_segment(self, topic: str, tone: str, transcript: str, tags: list) -> int:
        """
        Custom scoring logic for advertiser preferences.
        Heavily penalizes brand-unsafe content.
        """
        score = 3  # Start with neutral
        
        # Tone preferences (moderate influence)
        if tone.lower() in self.preferences.get("preferred_tones", []):
            score += 1
        if tone.lower() in self.preferences.get("disliked_tones", []):
            score -= 2  # Strong penalty for negative tones
        
        # Topic preferences (high commercial value topics)
        if topic.lower() in self.preferences.get("preferred_topics", []):
            score += 2  # Strong bonus for commercial topics
        
        # Brand safety is critical - harsh penalties
        brand_unsafe_tags = ["profanity", "controversial", "negative"]
        if any(tag in brand_unsafe_tags for tag in tags):
            score -= 2  # Major penalty for unsafe content
        
        # Specific brand safety checks
        if "profanity" in tags:
            score -= 2  # Additional penalty for profanity
        
        # Bonus for highly engaging tones
        if tone.lower() == "excited":
            score += 1
        
        # Technology and lifestyle are high-value topics
        if topic.lower() in ["technology", "lifestyle", "health"]:
            score += 1
        
        return max(1, min(score, 5))
    
    def generate_opinion(self, score: int, topic: str, tone: str) -> str:
        """Generate advertiser-appropriate opinions."""
        if score >= 4:
            return f"Excellent {topic} segment with strong commercial appeal - {tone} tone drives engagement and is brand-safe."
        elif score == 3:
            return f"Acceptable {topic} content but needs stronger {tone} elements to maximize advertiser value."
        else:
            return f"Limited advertiser appeal - {topic} segment with {tone} tone poses brand safety concerns."
    
    def generate_note(self, topic: str, tone: str, tags: list) -> str:
        """Generate advertiser-specific notes."""
        if "profanity" in tags:
            return "⚠️ BRAND SAFETY ISSUE: Contains profanity - not suitable for most advertisers"
        if "controversial" in tags:
            return "⚠️ BRAND SAFETY ISSUE: Controversial content - high risk for brand association"
        if "negative" in tags:
            return "Negative tone may reduce engagement and advertiser appeal"
        if topic.lower() in ["technology", "lifestyle", "health"]:
            return f"High commercial value: {topic} content attracts premium advertisers"
        return ""
    
    def estimate_confidence(self, score: int) -> float:
        """
        Advertisers have high confidence in their scoring (data-driven decisions).
        Override to increase confidence levels.
        """
        if score in [1, 5]:
            return 0.95  # Very confident in extreme scores
        elif score in [2, 4]:
            return 0.85  # Confident in clear preferences
        else:
            return 0.70  # Moderate confidence in neutral content
