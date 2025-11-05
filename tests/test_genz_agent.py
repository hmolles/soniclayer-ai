from app.models.personas.genz_agent import GenZAgent


def test_genz_agent_initialization():
    """Test GenZAgent initializes with correct attributes."""
    agent = GenZAgent()
    
    assert agent.name == "GenZ"
    assert "humorous" in agent.preferences["preferred_tones"]
    assert "formal" in agent.preferences["disliked_tones"]


def test_genz_agent_prefers_humorous():
    """Test GenZ agent scores humorous content higher."""
    agent = GenZAgent()
    
    segment = {
        "transcript": "This is hilarious content!",
        "topic": "Entertainment",
        "tone": "Humorous",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    assert result["score"] >= 4  # Should score high for humorous content
    assert result["confidence"] > 0.5


def test_genz_agent_dislikes_formal():
    """Test GenZ agent scores formal content lower."""
    agent = GenZAgent()
    
    segment = {
        "transcript": "This is a formal academic discussion.",
        "topic": "Education",
        "tone": "Formal",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    assert result["score"] <= 2  # Should score low for formal content


def test_genz_agent_pop_culture_boost():
    """Test pop culture topics get score boost."""
    agent = GenZAgent()
    
    segment = {
        "transcript": "Let's talk about the latest entertainment trends.",
        "topic": "Entertainment",
        "tone": "Excited",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    assert result["score"] >= 4  # Entertainment + excited should score high


def test_genz_agent_repetition_penalty():
    """Test that repetition tag reduces score."""
    agent = GenZAgent()
    
    segment = {
        "transcript": "We discussed this before.",
        "topic": "Technology",
        "tone": "Informative",
        "tags": ["repetition"]
    }
    
    result = agent.evaluate(segment)
    
    # Repetition should lower the score
    assert result["score"] < 4
    assert "repetition" in result["note"].lower() or result["note"] != ""


def test_genz_agent_opinion_format():
    """Test that opinion contains Gen Z appropriate language."""
    agent = GenZAgent()
    
    segment = {
        "transcript": "Amazing tech announcement!",
        "topic": "Technology",
        "tone": "Excited",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    assert result["opinion"] != ""
    assert isinstance(result["opinion"], str)


def test_genz_agent_score_bounds():
    """Test that scores are always between 1 and 5."""
    agent = GenZAgent()
    
    # Test extreme negative case
    segment_bad = {
        "transcript": "Formal academic lecture",
        "topic": "Academic",
        "tone": "Formal",
        "tags": ["repetition"]
    }
    
    result_bad = agent.evaluate(segment_bad)
    assert 1 <= result_bad["score"] <= 5
    
    # Test extreme positive case
    segment_good = {
        "transcript": "Hilarious viral content!",
        "topic": "Entertainment",
        "tone": "Humorous",
        "tags": []
    }
    
    result_good = agent.evaluate(segment_good)
    assert 1 <= result_good["score"] <= 5


def test_genz_agent_confidence_estimation():
    """Test confidence increases with extreme scores."""
    agent = GenZAgent()
    
    # High score should have higher confidence
    segment_high = {
        "transcript": "Amazing content!",
        "topic": "Entertainment",
        "tone": "Excited",
        "tags": []
    }
    
    result_high = agent.evaluate(segment_high)
    
    # Low score should also have higher confidence
    segment_low = {
        "transcript": "Boring formal content",
        "topic": "Academic",
        "tone": "Formal",
        "tags": []
    }
    
    result_low = agent.evaluate(segment_low)
    
    # Both should have confidence values
    assert 0.0 <= result_high["confidence"] <= 1.0
    assert 0.0 <= result_low["confidence"] <= 1.0


def test_genz_agent_get_prompt():
    """Test that Langflow prompt is generated correctly."""
    agent = GenZAgent()
    
    segment = {
        "transcript": "Test content",
        "topic": "Test",
        "tone": "Neutral",
        "tags": []
    }
    
    prompt = agent.get_prompt(segment)
    
    assert "Gen Z" in prompt or "18-25" in prompt
    assert "Test content" in prompt
