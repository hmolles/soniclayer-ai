# Persona & Worker Architecture Guide

**Last Updated:** 5 November 2025  
**Purpose:** Complete explanation of how personas and workers function in SonicLayer AI

---

## 📐 Architecture Overview

The persona evaluation system uses a **two-tier architecture**:

1. **PersonaAgent Base Class** - Python evaluation logic with scoring rules
2. **Langflow Chains** - LLM-powered natural language evaluation

### Data Flow

```
Audio Upload → Transcription → Classification → Worker Queue → Persona Evaluation → Redis Storage
                                                      ↓
                                            PersonaAgent (local)
                                                      +
                                            Langflow Chain (LLM)
```

---

## 🧩 Core Components

### 1. PersonaAgent Base Class
**File:** `app/models/personas/persona_agent.py`  
**Status:** ✅ Fully implemented  
**Purpose:** Provides evaluation framework for all personas

#### Key Methods

```python
class PersonaAgent:
    def __init__(self, name, description, preferences, rubric):
        # name: "GenZ" or "Advertiser"
        # description: What this persona represents
        # preferences: Dict of preferred_tones, preferred_topics, disliked_tags
        # rubric: Scoring criteria (currently unused, for future enhancements)
    
    def evaluate(self, segment) -> dict:
        """
        Main evaluation method - returns complete feedback
        Returns: {score, confidence, opinion, note, rationale}
        """
    
    def score_segment(self, topic, tone, transcript, tags) -> int:
        """
        Calculate numerical score (1-5) based on preferences
        - Starts at 3 (neutral)
        - +1 for preferred tone
        - +1 for preferred topic
        - -2 for disliked tags
        """
    
    def estimate_confidence(self, score) -> float:
        """
        Calculate confidence level (0.0-1.0)
        Formula: 0.5 + (abs(score - 3) / 4)
        - Score 1 or 5: ~0.75 confidence (strong opinion)
        - Score 3: 0.5 confidence (neutral)
        """
    
    def generate_rationale(self, score, topic, tone, transcript) -> str:
        """Generate explanation for the score"""
    
    def generate_opinion(self, score, topic, tone) -> str:
        """Generate one-sentence opinion"""
    
    def generate_note(self, topic, tone, tags) -> str:
        """Generate optional notes (repetition, profanity, etc.)"""
    
    def get_prompt(self, segment) -> str:
        """
        Generate LLM prompt for Langflow chain
        Used by Langflow to get natural language evaluation
        """
```

#### Why This Design?

- **Flexibility:** Can evaluate locally (fast) OR via LLM (nuanced)
- **Fallback:** If Langflow fails, local evaluation still works
- **Extensibility:** New personas just extend this class
- **Testing:** Easy to unit test without external dependencies

---

### 2. Persona Implementations

#### GenZAgent
**File:** `app/models/personas/genz_agent.py`  
**Status:** ✅ Fully implemented (13 unit tests)

**Preferences:**
```python
preferences = {
    "preferred_tones": ["humorous", "excited", "casual"],
    "preferred_topics": ["entertainment", "technology", "lifestyle", "food"],
    "disliked_tags": ["formal", "repetition"],
    "name": "GenZ",
    "description": "Gen Z listener seeking engaging, energetic content"
}
```

**Characteristics:**
- Loves humorous and excited content
- Interested in pop culture, tech, lifestyle
- Dislikes formal or repetitive segments
- High engagement threshold

**Example Evaluation:**
```python
segment = {
    "text": "Check out this hilarious new meme trend!",
    "topic": "Entertainment",
    "tone": "Humorous"
}
# Result: Score 5, Opinion: "Totally vibing with this!", Confidence: 0.75
```

#### AdvertiserAgent
**File:** `app/models/personas/advertiser_agent.py`  
**Status:** ✅ Fully implemented (13 unit tests)

**Preferences:**
```python
preferences = {
    "preferred_tones": ["excited", "informative", "positive"],
    "preferred_topics": ["technology", "food", "lifestyle", "health"],
    "disliked_tags": ["profanity", "controversial", "negative"],
    "name": "Advertiser",
    "description": "Brand safety focused advertiser seeking positive content"
}
```

**Characteristics:**
- Brand safety is priority #1
- Prefers positive, informative content
- Strong penalties for profanity or controversial topics
- Higher confidence scores (0.65 vs 0.5 base)

**Example Evaluation:**
```python
segment = {
    "text": "This damn product is controversial",
    "topic": "Technology",
    "tone": "Controversial",
    "tags": ["profanity"]
}
# Result: Score 1, Opinion: "Unsafe for brand placement", Confidence: 0.75
```

---

### 3. Worker Files

Workers are **RQ background jobs** that process segments asynchronously.

#### GenZ Worker
**File:** `app/workers/genz_worker.py`  
**Status:** ✅ Operational (uses Langflow)

**Function Signature:**
```python
def process_transcript(audio_id, transcript_segments, classifier_results):
    """
    Args:
        audio_id: SHA256 hash of audio file (e.g., "ebeb6435...")
        transcript_segments: List of dicts with 'text', 'start', 'end'
        classifier_results: List of dicts with 'topic', 'tone', 'tags'
    
    Returns:
        List of feedback dicts with GenZ evaluations
    """
```

**Process Flow:**
1. Loop through each segment
2. Build JSON input: `{text, topic, tone}`
3. Call Langflow chain: `call_langflow_chain("genz_chain", segment_input)`
4. Parse LLM response
5. Store in Redis: `persona_feedback:genz:{audio_id}:{segment_id}`
6. Handle errors with fallback scores

**Redis Keys Created:**
- `persona_feedback:genz:{audio_id}:{segment_id}` - Individual segment feedback
- `persona_feedback:genz:{audio_id}` - Aggregated all-segment feedback
- TTL: 24 hours (86400 seconds)

**Error Handling:**
```python
try:
    result = call_langflow_chain("genz_chain", segment_input)
except Exception as e:
    # Fallback to default response
    result = {
        "score": 3,
        "opinion": "Unable to evaluate",
        "rationale": f"Error: {str(e)}",
        "confidence": 0.0,
        "note": "Langflow call failed"
    }
```

#### Advertiser Worker
**File:** `app/workers/advertiser_worker.py`  
**Status:** ✅ Operational (uses Langflow)

**Identical structure to GenZ worker**, but:
- Calls `advertiser_chain` in Langflow
- Stores to `persona_feedback:advertiser:{audio_id}:{segment_id}`
- Uses AdvertiserAgent preferences for scoring

#### Parents Worker
**File:** `app/workers/parents_worker.py`  
**Status:** ⚠️ **NOT IMPLEMENTED** (placeholder only)

**Current State:**
- File exists with basic worker structure
- Does NOT use PersonaAgent base class
- Does NOT have Langflow chain configured
- NOT queued by `/evaluate/` endpoint

**To Implement:**
1. Create `ParentsAgent` class extending PersonaAgent
2. Define parent-friendly preferences (family-safe, educational)
3. Create `parents_chain` in Langflow
4. Update worker to use new agent
5. Add to queue in `app/routes/evaluate.py`

#### Regional Worker
**File:** `app/workers/regional_worker.py`  
**Status:** ⚠️ **NOT IMPLEMENTED** (placeholder only)

**Same status as Parents Worker** - exists but not functional.

---

## 🔄 Complete Request Flow

### Step 1: Audio Upload
**Endpoint:** `POST /evaluate/`  
**File:** `app/routes/evaluate.py`

```python
1. User uploads WAV file
2. Generate audio_id = SHA256(audio_bytes)
3. Save to uploads/{audio_id}.wav
4. Check Redis cache for existing processing
```

### Step 2: Transcription
**Service:** `app/services/transcryption.py`

```python
5. Call Whisper with word_timestamps=True
6. Group segments by ~15 second duration
7. Return list: [{start, end, text}, ...]
```

**Example Output:**
```json
[
  {"start": 0.0, "end": 14.5, "text": "Welcome to the show..."},
  {"start": 14.5, "end": 28.3, "text": "Today we're talking about..."}
]
```

### Step 3: Classification
**Service:** `app/services/classifier.py`

```python
8. For each segment, call HuggingFace BART
9. Classify topic: ["Health", "Entertainment", "Politics", "Technology", "Food", "Education"]
10. Classify tone: ["Informative", "Humorous", "Excited", "Neutral", "Controversial"]
```

**Example Output:**
```json
{
  "segment_id": 0,
  "start": 0.0,
  "end": 14.5,
  "text": "Welcome to the show...",
  "topic": "Entertainment",
  "tone": "Excited",
  "tags": []
}
```

### Step 4: Store in Redis
**Cache:** `app/services/cache.py`

```python
11. Store transcript_segments:{audio_id}
12. Store classifier_output:{audio_id}
13. TTL: 24 hours
```

### Step 5: Queue Worker Jobs
**Queue:** RQ (Redis Queue)

```python
14. queue.enqueue(genz_process, audio_id, transcript_segments, classifier_results)
15. queue.enqueue(advertiser_process, audio_id, transcript_segments, classifier_results)
16. Return job_ids to client
```

**Response to User:**
```json
{
  "audio_id": "ebeb643592f3ae...",
  "status": "processing",
  "segment_count": 14,
  "transcript_length": 2847,
  "job_ids": {
    "genz": "job-abc-123",
    "advertiser": "job-def-456"
  }
}
```

### Step 6: Worker Processing (Async)
**Workers:** `genz_worker.py`, `advertiser_worker.py`

```python
17. Worker picks up job from queue
18. For each segment:
    a. Build segment input JSON
    b. Call Langflow API
    c. Parse LLM response
    d. Store feedback in Redis
19. Job completes
```

**Langflow API Call:**
```python
POST http://localhost:7860/api/v1/run/genz_chain
Headers: {
  "x-api-key": "sk-pYbkputG...",
  "Content-Type": "application/json"
}
Body: {
  "input_value": '{"text": "...", "topic": "Entertainment", "tone": "Excited"}',
  "output_type": "chat",
  "input_type": "chat"
}
```

**Langflow Response:**
```json
{
  "outputs": [{
    "outputs": [{
      "results": {
        "message": {
          "text": "Rating: 5\nOpinion: Totally vibing with this!\nNote: \nRationale: Excited tone matches GenZ preferences"
        }
      }
    }]
  }]
}
```

### Step 7: Retrieval
**Endpoint:** `GET /segments/{audio_id}`  
**File:** `app/routes/segments.py`

```python
20. Fetch transcript_segments from Redis
21. Fetch classifier_output from Redis
22. For each segment:
    a. Fetch persona_feedback:genz:{audio_id}:{i}
    b. Fetch persona_feedback:advertiser:{audio_id}:{i}
    c. Merge all data into enriched segment
23. Return complete segments array
```

**Response:**
```json
[
  {
    "segment_id": 0,
    "start": 0.0,
    "end": 14.5,
    "transcript": "Welcome to the show...",
    "topic": "Entertainment",
    "tone": "Excited",
    "genz": {
      "score": 5,
      "opinion": "Totally vibing with this!",
      "confidence": 0.75,
      "rationale": "Excited tone matches GenZ preferences",
      "note": ""
    },
    "advertiser": {
      "score": 4,
      "opinion": "Good energy, brand-safe content",
      "confidence": 0.65,
      "rationale": "Positive tone, entertainment topic aligns well",
      "note": ""
    }
  }
]
```

---

## 🗂️ File Usage Summary

### ✅ ACTIVELY USED

| File | Purpose | Called By | Status |
|------|---------|-----------|--------|
| `persona_agent.py` | Base class for all personas | GenZAgent, AdvertiserAgent | ✅ Production |
| `genz_agent.py` | GenZ evaluation logic | genz_worker.py | ✅ Production |
| `advertiser_agent.py` | Advertiser evaluation logic | advertiser_worker.py | ✅ Production |
| `genz_worker.py` | Process segments via GenZ Langflow chain | RQ queue from /evaluate/ | ✅ Production |
| `advertiser_worker.py` | Process segments via Advertiser Langflow chain | RQ queue from /evaluate/ | ✅ Production |

### ⚠️ EXIST BUT NOT USED

| File | Purpose | Status | Action Needed |
|------|---------|--------|---------------|
| `parents_worker.py` | Family-friendly evaluation | ⚠️ Placeholder | Create ParentsAgent + Langflow chain |
| `regional_worker.py` | Geographic/cultural evaluation | ⚠️ Placeholder | Create RegionalAgent + Langflow chain |

### 🔧 SUPPORTING FILES

| File | Purpose | Used By |
|------|---------|---------|
| `app/services/langflow_client.py` | Call Langflow API | All workers |
| `app/services/classifier.py` | HuggingFace topic/tone classification | /evaluate/ endpoint |
| `app/services/transcryption.py` | Whisper transcription | /evaluate/ endpoint |
| `app/services/cache.py` | Redis connection | All workers, all routes |
| `app/routes/evaluate.py` | Upload endpoint | User upload |
| `app/routes/segments.py` | Retrieval endpoint | Dashboard, API clients |

---

## 🎭 Current Active Personas

### Production (Working)
1. **GenZ** - Youth demographic targeting
2. **Advertiser** - Brand safety and commercial viability

### Planned (Not Implemented)
3. **Parents** - Family-friendly content evaluation
4. **Regional** - Geographic/cultural appropriateness

---

## 🔌 Langflow Integration

### Chain Requirements

Each persona needs a corresponding Langflow chain:

**GenZ Chain Name:** `genz_chain`  
**Advertiser Chain Name:** `advertiser_chain`

### Chain Structure
1. **Chat Input** - Receives segment JSON
2. **Prompt Template** - Uses PersonaAgent.get_prompt() format
3. **LLM Component** - Connects to LM Studio (localhost:1234)
4. **Chat Output** - Returns formatted response

### Expected Response Format
```
Rating: 5
Opinion: This segment is fire! 🔥
Note: Great energy and relevant topic
Rationale: Excited tone and entertainment topic match GenZ preferences perfectly
```

### Parsing in Worker
```python
lines = response.strip().split("\n")
result = {
    "score": int(lines[0].split(":")[1].strip()),
    "opinion": lines[1].split(":")[1].strip(),
    "note": lines[2].split(":")[1].strip(),
    "rationale": lines[3].split(":")[1].strip()
}
```

---

## 🧪 Testing Strategy

### Unit Tests (Per Persona)
- Test scoring logic with different topics/tones
- Test edge cases (empty text, missing fields)
- Test confidence calculation
- Test opinion/rationale generation

**Files:**
- `tests/test_persona_agent.py` - Base class (12 tests)
- `tests/test_genz_agent.py` - GenZ specific (13 tests)
- `tests/test_advertiser_agent.py` - Advertiser specific (13 tests)

### Integration Tests
- Mock Langflow API responses
- Test worker error handling
- Test Redis storage/retrieval
- Test complete pipeline

**File:** `scripts/integration_test.py`

---

## 🚀 Adding a New Persona

### Step 1: Create Agent Class
```python
# app/models/personas/parents_agent.py
from app.models.personas.persona_agent import PersonaAgent

class ParentsAgent(PersonaAgent):
    def __init__(self):
        preferences = {
            "preferred_tones": ["informative", "positive", "educational"],
            "preferred_topics": ["education", "health", "family", "lifestyle"],
            "disliked_tags": ["profanity", "controversial", "violent"],
            "name": "Parents",
            "description": "Parent seeking family-friendly, educational content"
        }
        
        rubric = {
            "family_safety": 5,
            "educational_value": 4,
            "age_appropriate": 5
        }
        
        super().__init__(
            name="Parents",
            description="Parent seeking family-friendly content",
            preferences=preferences,
            rubric=rubric
        )
    
    # Optional: Override methods for custom logic
    def score_segment(self, topic, tone, transcript, tags):
        score = super().score_segment(topic, tone, transcript, tags)
        # Custom: Extra penalty for violence
        if "violent" in tags:
            score -= 2
        return max(1, min(score, 5))
```

### Step 2: Create Worker
```python
# app/workers/parents_worker.py
from app.services.langflow_client import call_langflow_chain
from app.services.cache import redis_conn
import json

def process_transcript(audio_id, transcript_segments, classifier_results):
    for i, segment in enumerate(transcript_segments):
        segment_input = json.dumps({
            "text": segment.get("text", ""),
            "topic": classifier_results[i].get("topic", ""),
            "tone": classifier_results[i].get("tone", "")
        })
        
        try:
            result = call_langflow_chain("parents_chain", segment_input)
        except Exception as e:
            result = {"score": 3, "opinion": "Unable to evaluate", ...}
        
        redis_conn.set(
            f"persona_feedback:parents:{audio_id}:{i}",
            json.dumps(result),
            ex=86400
        )
```

### Step 3: Create Langflow Chain
1. Open Langflow at http://localhost:7860
2. Create new flow named `parents_chain`
3. Add components: Chat Input → Prompt → LLM → Chat Output
4. Configure prompt with ParentsAgent preferences
5. Test with sample segment

### Step 4: Queue in Evaluate Endpoint
```python
# app/routes/evaluate.py
from app.workers.parents_worker import process_transcript as parents_process

# In evaluate_audio function:
parents_job = queue.enqueue(
    parents_process,
    audio_id,
    transcript_segments,
    classifier_results
)
```

### Step 5: Update Segments Endpoint
```python
# app/routes/segments.py
# In extract_segments function:
parents_feedback = redis_conn.get(f"persona_feedback:parents:{audio_id}:{i}")
if parents_feedback:
    segment["parents"] = json.loads(parents_feedback)
```

### Step 6: Write Tests
```python
# tests/test_parents_agent.py
def test_parents_agent_family_safe():
    agent = ParentsAgent()
    segment = {
        "topic": "Education",
        "tone": "Informative",
        "transcript": "Today we learn about science",
        "tags": []
    }
    result = agent.evaluate(segment)
    assert result["score"] >= 4
```

---

## 📊 Performance Considerations

### Current Bottlenecks
1. **Whisper Transcription** - 30-60 seconds for 2-minute audio
2. **Langflow LLM Calls** - 2-5 seconds per segment
3. **Total Processing** - 1-3 minutes for 14 segments (2 personas × 14 calls)

### Optimization Strategies
1. **Parallel Worker Execution** - Already implemented (RQ runs GenZ and Advertiser in parallel)
2. **Batch Langflow Calls** - Future: Send multiple segments in one request
3. **Cache Model Loads** - Keep Whisper/BART in memory (currently done)
4. **Reduce Segment Count** - Use 20-30 second segments instead of 15

---

## 🔑 Key Takeaways

1. **PersonaAgent** is the foundation - all personas extend it
2. **Workers** are RQ background jobs that call Langflow
3. **Langflow chains** provide LLM-powered natural language evaluation
4. **Redis** stores all intermediate and final results
5. **Only GenZ and Advertiser** are currently operational
6. **Adding new personas** follows a clear 6-step pattern
7. **Error handling** ensures system never fully fails (fallback scores)

---

## 📚 Related Documentation

- [TODO.md](TODO.md) - Next steps for additional personas
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current implementation status
- [docs/LANGFLOW_SETUP_GUIDE.md](docs/LANGFLOW_SETUP_GUIDE.md) - Chain configuration
- [CLASSIFICATION_STRATEGY.md](CLASSIFICATION_STRATEGY.md) - Topic/tone classification details
