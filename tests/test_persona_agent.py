from app.models.personas.persona_agent import PersonaAgent


def test_persona_agent_initialization():
    """Test PersonaAgent can be initialized with basic parameters."""
    agent = PersonaAgent(
        name="Test",
        description="A test persona",
        preferences={"preferred_tones": ["neutral"]},
        rubric={"accuracy": 1.0}
    )
    
    assert agent.name == "Test"
    assert agent.description == "A test persona"


def test_persona_agent_score_segment():
    """Test basic scoring logic."""
    agent = PersonaAgent(
        name="Test",
        description="Test",
        preferences={
            "preferred_tones": ["informative"],
            "preferred_topics": ["technology"],
            "disliked_tags": ["profanity"]
        },
        rubric={}
    )
    
    score = agent.score_segment("Technology", "Informative", "Test transcript", [])
    
    assert 1 <= score <= 5
    assert score >= 3  # Should be positive for preferred topic and tone


def test_persona_agent_estimate_confidence():
    """Test confidence calculation (0.5 to 1.0)."""
    agent = PersonaAgent("Test", "Test", {}, {})
    
    # Neutral score (3) should have lower confidence
    conf_neutral = agent.estimate_confidence(3)
    assert 0.5 <= conf_neutral <= 0.6
    
    # Extreme scores (1, 5) should have higher confidence
    conf_high = agent.estimate_confidence(5)
    assert conf_high > conf_neutral
    
    conf_low = agent.estimate_confidence(1)
    assert conf_low > conf_neutral


def test_persona_agent_generate_rationale():
    """Test rationale string generation."""
    agent = PersonaAgent("Test", "Test", {}, {})
    
    rationale = agent.generate_rationale(4, "Technology", "Excited", "Great tech!")
    
    assert isinstance(rationale, str)
    assert len(rationale) > 0
    assert "Technology" in rationale or "technology" in rationale.lower()


def test_persona_agent_generate_opinion():
    """Test opinion generation for different scores."""
    agent = PersonaAgent("Test", "Test", {}, {})
    
    # High score
    opinion_high = agent.generate_opinion(5, "Technology", "Excited")
    assert "engaging" in opinion_high.lower() or "well-targeted" in opinion_high.lower()
    
    # Neutral score
    opinion_neutral = agent.generate_opinion(3, "Technology", "Neutral")
    assert "acceptable" in opinion_neutral.lower()
    
    # Low score
    opinion_low = agent.generate_opinion(1, "Technology", "Boring")
    assert "misaligned" in opinion_low.lower() or "felt" in opinion_low.lower()


def test_persona_agent_generate_note():
    """Test note generation for tags."""
    agent = PersonaAgent("Test", "Test", {}, {})
    
    # Repetition tag
    note_rep = agent.generate_note("Test", "Test", ["repetition"])
    assert "repeated" in note_rep.lower()
    
    # Profanity tag
    note_prof = agent.generate_note("Test", "Test", ["profanity"])
    assert "offensive" in note_prof.lower() or "language" in note_prof.lower()
    
    # No tags
    note_clean = agent.generate_note("Test", "Test", [])
    assert note_clean == ""


def test_persona_agent_evaluate():
    """Test full evaluation pipeline."""
    agent = PersonaAgent(
        name="Test",
        description="Test",
        preferences={
            "preferred_tones": ["informative"],
            "preferred_topics": ["technology"]
        },
        rubric={}
    )
    
    segment = {
        "topic": "Technology",
        "tone": "Informative",
        "transcript": "Great tech content",
        "tags": []
    }
    
    result = agent.evaluate(segment)
    
    assert "score" in result
    assert "confidence" in result
    assert "opinion" in result
    assert "note" in result
    assert "rationale" in result
    
    assert 1 <= result["score"] <= 5
    assert 0.0 <= result["confidence"] <= 1.0


def test_persona_agent_get_prompt():
    """Test Langflow prompt formatting."""
    agent = PersonaAgent(
        name="Test",
        description="a test agent for evaluation",
        preferences={},
        rubric={}
    )
    
    segment = {
        "transcript": "This is test content",
        "topic": "Test",
        "tone": "Neutral",
        "tags": ["test_tag"]
    }
    
    prompt = agent.get_prompt(segment)
    
    assert isinstance(prompt, str)
    assert "test agent" in prompt.lower()
    assert "This is test content" in prompt
    assert "Test" in prompt


def test_persona_agent_disliked_tags_penalty():
    """Test that disliked tags reduce score."""
    agent = PersonaAgent(
        name="Test",
        description="Test",
        preferences={
            "preferred_tones": ["neutral"],
            "disliked_tags": ["bad_tag"]
        },
        rubric={}
    )
    
    # Without disliked tag
    score_clean = agent.score_segment("Test", "Neutral", "Content", [])
    
    # With disliked tag
    score_tagged = agent.score_segment("Test", "Neutral", "Content", ["bad_tag"])
    
    assert score_tagged < score_clean


def test_persona_agent_parse_llm_response():
    """Test parsing LLM response format."""
    agent = PersonaAgent("Test", "Test", {}, {})
    
    response = """Rating: 4
Opinion: This is a good segment
Note: No issues
Rationale: Scored well because of quality"""
    
    result = agent.parse_llm_response(response)
    
    assert result["score"] == 4
    assert "good segment" in result["opinion"]
    assert "No issues" in result["note"]
    assert "quality" in result["rationale"]
