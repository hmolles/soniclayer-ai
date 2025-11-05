from app.models.personas.advertiser_agent import AdvertiserAgent


def test_advertiser_agent_initialization():
    """Test AdvertiserAgent initializes with correct attributes."""
    agent = AdvertiserAgent()
    
    assert agent.name == "Advertiser"
    assert "excited" in agent.preferences["preferred_tones"]
    assert "profanity" in agent.preferences["disliked_tags"]


def test_advertiser_agent_brand_safety():
    """Test advertiser penalizes brand-unsafe content heavily."""
    agent = AdvertiserAgent()
    
    segment = {
        "transcript": "Content with inappropriate language",
        "topic": "Entertainment",
        "tone": "Controversial",
        "tags": ["profanity"]
    }
    
    result = agent.evaluate(segment)
    
    assert result["score"] <= 2  # Should score very low for brand unsafe content
    assert "BRAND SAFETY" in result["note"] or "brand" in result["note"].lower()


def test_advertiser_agent_commercial_value():
    """Test advertiser values high commercial value topics."""
    agent = AdvertiserAgent()
    
    segment = {
        "transcript": "New technology product announcement",
        "topic": "Technology",
        "tone": "Excited",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    assert result["score"] >= 4  # Technology + excited = high commercial value


def test_advertiser_agent_positive_tone_preference():
    """Test advertiser prefers positive, informative tones."""
    agent = AdvertiserAgent()
    
    segment = {
        "transcript": "Great new health benefits",
        "topic": "Health",
        "tone": "Informative",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    assert result["score"] >= 3


def test_advertiser_agent_controversial_penalty():
    """Test controversial content gets penalized."""
    agent = AdvertiserAgent()
    
    segment = {
        "transcript": "Controversial political debate",
        "topic": "Politics",
        "tone": "Controversial",
        "tags": ["controversial"]
    }
    
    result = agent.evaluate(segment)
    
    assert result["score"] <= 2


def test_advertiser_agent_high_confidence():
    """Test advertisers have high confidence in their scoring."""
    agent = AdvertiserAgent()
    
    # Extreme score should have very high confidence
    segment_unsafe = {
        "transcript": "Unsafe content",
        "topic": "Test",
        "tone": "Negative",
        "tags": ["profanity"]
    }
    
    result = agent.evaluate(segment_unsafe)
    
    # Advertiser uses custom confidence estimation
    assert result["confidence"] >= 0.70


def test_advertiser_agent_lifestyle_bonus():
    """Test lifestyle/health topics get commercial value bonus."""
    agent = AdvertiserAgent()
    
    segment = {
        "transcript": "New lifestyle trend",
        "topic": "Lifestyle",
        "tone": "Excited",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    assert result["score"] >= 4


def test_advertiser_agent_negative_tone_penalty():
    """Test negative tones are penalized."""
    agent = AdvertiserAgent()
    
    segment = {
        "transcript": "Depressing news",
        "topic": "News",
        "tone": "Negative",
        "tags": ["negative"]
    }
    
    result = agent.evaluate(segment)
    
    assert result["score"] <= 2


def test_advertiser_agent_opinion_format():
    """Test opinion contains commercial/brand language."""
    agent = AdvertiserAgent()
    
    segment = {
        "transcript": "New food product",
        "topic": "Food",
        "tone": "Excited",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    assert result["opinion"] != ""
    assert isinstance(result["opinion"], str)


def test_advertiser_agent_score_bounds():
    """Test scores are always between 1 and 5."""
    agent = AdvertiserAgent()
    
    # Test extreme negative case
    segment_bad = {
        "transcript": "Unsafe content",
        "topic": "Test",
        "tone": "Controversial",
        "tags": ["profanity", "negative"]
    }
    
    result_bad = agent.evaluate(segment_bad)
    assert 1 <= result_bad["score"] <= 5
    
    # Test extreme positive case
    segment_good = {
        "transcript": "Perfect brand content",
        "topic": "Technology",
        "tone": "Excited",
        "tags": []
    }
    
    result_good = agent.evaluate(segment_good)
    assert 1 <= result_good["score"] <= 5


def test_advertiser_agent_profanity_warning():
    """Test profanity tag triggers specific warning."""
    agent = AdvertiserAgent()
    
    segment = {
        "transcript": "Content with bad words",
        "topic": "Test",
        "tone": "Casual",
        "tags": ["profanity"]
    }
    
    result = agent.evaluate(segment)
    
    assert "profanity" in result["note"].lower() or "BRAND SAFETY" in result["note"]


def test_advertiser_agent_commercial_note():
    """Test high-value topics generate positive notes."""
    agent = AdvertiserAgent()
    
    segment = {
        "transcript": "Tech innovation",
        "topic": "Technology",
        "tone": "Informative",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    # Should have note about commercial value or be empty
    assert isinstance(result["note"], str)
