# Classification & Labeling Strategy

**Last Updated:** 5 November 2025  
**Purpose:** Explain current classification approach and improvement strategies

---

## 📊 Current Classification System

### Overview

SonicLayer AI uses **zero-shot classification** with HuggingFace transformers to label audio segments with topic and tone categories.

**Model:** `facebook/bart-large-mnli`  
**Approach:** Zero-shot (no training required)  
**File:** `app/services/classifier.py`

---

## 🎯 Current Implementation

### Code

```python
from transformers import pipeline

# Load zero-shot classification pipelines (loaded once at startup)
topic_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
tone_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Predefined label sets
TOPIC_LABELS = ["Health", "Entertainment", "Politics", "Technology", "Food", "Education"]
TONE_LABELS = ["Informative", "Humorous", "Excited", "Neutral", "Controversial"]

def classify_segment(text: str) -> dict:
    """
    Classify a single segment for topic and tone.
    
    Args:
        text: Transcript text from segment
    
    Returns:
        {
            "topic": str,  # Most likely topic
            "tone": str    # Most likely tone
        }
    """
    topic_result = topic_classifier(text, TOPIC_LABELS)
    tone_result = tone_classifier(text, TONE_LABELS)

    return {
        "topic": topic_result["labels"][0],  # Top prediction
        "tone": tone_result["labels"][0]     # Top prediction
    }
```

### Label Categories

#### Topics (6 categories)
1. **Health** - Medical, fitness, wellness, mental health
2. **Entertainment** - Music, movies, TV, celebrities, pop culture
3. **Politics** - Government, elections, policy, current events
4. **Technology** - Gadgets, software, AI, innovation
5. **Food** - Recipes, restaurants, cooking, nutrition
6. **Education** - Learning, schools, tutorials, knowledge

#### Tones (5 categories)
1. **Informative** - Factual, educational, explanatory
2. **Humorous** - Funny, comedic, lighthearted
3. **Excited** - Energetic, enthusiastic, passionate
4. **Neutral** - Balanced, objective, calm
5. **Controversial** - Divisive, provocative, argumentative

---

## ⚙️ How It Works

### Zero-Shot Classification

**Concept:** BART model determines which label best matches the text **without training** on audio-specific data.

**Process:**
1. Model receives transcript text: `"Check out this new smartphone with AI features"`
2. Model compares text to each topic label
3. Returns probability scores:
   ```python
   {
     "Technology": 0.89,
     "Entertainment": 0.05,
     "Education": 0.03,
     "Politics": 0.02,
     "Food": 0.01,
     "Health": 0.00
   }
   ```
4. System picks highest: `"Technology"`

### Performance

**Speed:** ~200-500ms per segment (CPU)  
**Accuracy:** ~70-80% for clear, domain-specific content  
**Limitations:** 
- Struggles with ambiguous or multi-topic segments
- Limited to predefined labels
- No confidence scores used (only top prediction)

---

## 📈 Current Process Flow

### In `/evaluate/` Endpoint

```python
# After transcription completes...
classifier_results = []
for idx, segment in enumerate(transcript_segments):
    try:
        classification = classify_segment(segment["text"])
        classifier_results.append({
            "segment_id": idx,
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"],
            "topic": classification.get("topic", "Unknown"),
            "tone": classification.get("tone", "Unknown"),
            "tags": classification.get("tags", [])  # Currently empty
        })
    except Exception as e:
        logger.error(f"Classification failed for segment {idx}: {e}")
        classifier_results.append({
            "segment_id": idx,
            "topic": "Unknown",
            "tone": "Unknown",
            "tags": []
        })

# Store in Redis
redis_conn.set(
    f"classifier_output:{audio_id}",
    json.dumps(classifier_results),
    ex=86400  # 24 hour TTL
)
```

### Usage in Workers

Workers receive `classifier_results` and use topic/tone to evaluate segments:

```python
# In genz_worker.py
segment_input = json.dumps({
    "text": segment.get("text", ""),
    "topic": classifier_results[i].get("topic", ""),  # ← Used here
    "tone": classifier_results[i].get("tone", "")     # ← Used here
})

result = call_langflow_chain("genz_chain", segment_input)
```

Langflow LLM uses these classifications to provide context-aware persona feedback.

---

## ⚠️ Current Limitations

### 1. Fixed Label Set
**Problem:** Only 6 topics and 5 tones  
**Impact:** Nuanced content gets forced into broad categories  
**Example:** "Sports" segment labeled as "Entertainment"

### 2. Single Label per Segment
**Problem:** No multi-label support  
**Impact:** Segment about "healthy food recipes" must choose Health OR Food  
**Current Behavior:** Picks highest probability, ignores second-best

### 3. No Confidence Thresholds
**Problem:** System always picks a label, even if model is uncertain  
**Impact:** Low-confidence predictions treated same as high-confidence  
**Example:** Model 51% sure → still returns that label

### 4. No Tag Generation
**Problem:** Tags field always empty `[]`  
**Impact:** Can't detect profanity, repetition, or content warnings  
**Current Code:** `"tags": classification.get("tags", [])`  ← Always empty

### 5. Topic/Tone Only
**Problem:** Missing other useful dimensions  
**Impact:** No detection of:
- Sentiment (positive/negative/neutral)
- Emotion (happy/sad/angry)
- Formality (casual/professional)
- Target audience (kids/adults/seniors)
- Content warnings (violence/profanity/sensitive)

### 6. Model Size vs Speed
**Problem:** BART-large-mnli is 400MB+, runs on CPU  
**Impact:** Each classification takes 200-500ms  
**For 14 segments:** 2.8-7 seconds just for classification

---

## 🚀 Improvement Strategies

### Strategy 1: Expand Label Sets ⭐ **Easiest**

**Complexity:** Low (1 hour)  
**Impact:** Medium  
**Cost:** Free

**Implementation:**
```python
# Enhanced topic labels
TOPIC_LABELS = [
    "Health", "Entertainment", "Politics", "Technology", 
    "Food", "Education", "Sports", "Business", "Science",
    "Travel", "Fashion", "Relationships", "Finance", "News"
]

# Enhanced tone labels
TONE_LABELS = [
    "Informative", "Humorous", "Excited", "Neutral", 
    "Controversial", "Sarcastic", "Serious", "Casual",
    "Professional", "Emotional", "Motivational"
]
```

**Pros:**
- No code changes needed (just edit lists)
- Immediately more granular
- Better persona matching

**Cons:**
- More labels = slightly slower classification
- Still limited to predefined categories

---

### Strategy 2: Multi-Label Classification ⭐⭐ **Recommended**

**Complexity:** Medium (3-4 hours)  
**Impact:** High  
**Cost:** Free

**Implementation:**
```python
def classify_segment_multilabel(text: str, threshold: float = 0.3) -> dict:
    """
    Return multiple labels if confidence > threshold.
    
    Returns:
        {
            "topics": ["Technology", "Education"],  # Multiple topics
            "topic_scores": {"Technology": 0.85, "Education": 0.42},
            "tones": ["Informative", "Excited"],
            "tone_scores": {"Informative": 0.78, "Excited": 0.45}
        }
    """
    topic_result = topic_classifier(text, TOPIC_LABELS)
    tone_result = tone_classifier(text, TONE_LABELS)
    
    # Get all labels above threshold
    topics = [
        label for label, score in zip(topic_result["labels"], topic_result["scores"])
        if score >= threshold
    ]
    
    tones = [
        label for label, score in zip(tone_result["labels"], tone_result["scores"])
        if score >= threshold
    ]
    
    return {
        "topics": topics,
        "primary_topic": topics[0] if topics else "Unknown",
        "topic_scores": dict(zip(topic_result["labels"], topic_result["scores"])),
        "tones": tones,
        "primary_tone": tones[0] if tones else "Unknown",
        "tone_scores": dict(zip(tone_result["labels"], tone_result["scores"]))
    }
```

**Pros:**
- Captures nuanced content
- Provides confidence scores for better decision-making
- Personas can use secondary labels

**Cons:**
- Slightly more complex worker logic
- Need to update dashboard to show multiple labels

**Dashboard Update:**
```python
# Instead of: <Badge>{segment["topic"]}</Badge>
# Show: {segment["topics"].map(t => <Badge key={t}>{t}</Badge>)}
```

---

### Strategy 3: Add Content Warning Tags ⭐⭐⭐ **Important**

**Complexity:** Medium (2-3 hours)  
**Impact:** High (brand safety)  
**Cost:** Free

**Implementation:**
```python
# New tag detection pipelines
profanity_classifier = pipeline("text-classification", model="unitary/toxic-bert")
sentiment_classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

def detect_tags(text: str) -> list:
    """
    Detect content warnings and special attributes.
    
    Returns:
        ["profanity", "negative_sentiment", "repetition"]
    """
    tags = []
    
    # Profanity detection
    try:
        toxicity = profanity_classifier(text)[0]
        if toxicity["label"] == "toxic" and toxicity["score"] > 0.7:
            tags.append("profanity")
    except:
        pass
    
    # Sentiment
    try:
        sentiment = sentiment_classifier(text)[0]
        if sentiment["label"] == "NEGATIVE" and sentiment["score"] > 0.8:
            tags.append("negative_sentiment")
    except:
        pass
    
    # Repetition detection (simple heuristic)
    if len(set(text.split())) / len(text.split()) < 0.3:  # Low unique word ratio
        tags.append("repetition")
    
    # Length-based tags
    if len(text.strip()) < 20:
        tags.append("instrumental")  # Already handled in dashboard
    
    return tags

# Update classify_segment
def classify_segment(text: str) -> dict:
    topic_result = topic_classifier(text, TOPIC_LABELS)
    tone_result = tone_classifier(text, TONE_LABELS)
    tags = detect_tags(text)  # ← Add this
    
    return {
        "topic": topic_result["labels"][0],
        "tone": tone_result["labels"][0],
        "tags": tags  # ← Now populated
    }
```

**New Dependencies:**
```bash
pip install unitary/toxic-bert distilbert-base-uncased-finetuned-sst-2-english
```

**Pros:**
- Critical for advertiser brand safety
- Helps parents persona filter content
- Improves persona scoring accuracy

**Cons:**
- Additional model downloads (~500MB)
- Slower classification (3 models instead of 2)

---

### Strategy 4: LLM-Based Classification ⭐⭐⭐⭐ **Most Powerful**

**Complexity:** Medium-High (4-6 hours)  
**Impact:** Very High  
**Cost:** Free (local LLM) or $$ (API calls)

**Implementation:**
```python
def classify_segment_llm(text: str) -> dict:
    """
    Use LLM for rich, open-ended classification.
    """
    prompt = f"""
    Analyze this radio segment transcript and provide:
    1. Primary topic (be specific, not limited to predefined categories)
    2. Secondary topics (if any)
    3. Tone/style
    4. Target audience
    5. Content warnings (profanity, controversy, etc.)
    6. Sentiment
    7. Key themes or messages
    
    Transcript: {text}
    
    Respond in JSON format:
    {{
        "primary_topic": "...",
        "secondary_topics": [...],
        "tone": "...",
        "audience": "...",
        "warnings": [...],
        "sentiment": "positive/negative/neutral",
        "themes": [...]
    }}
    """
    
    # Call local LM Studio or Langflow
    response = call_langflow_chain("classifier_chain", prompt)
    return json.loads(response)
```

**Pros:**
- No predefined labels - truly flexible
- Can detect nuanced themes
- Natural language descriptions
- Context-aware (understands cultural references)

**Cons:**
- Slower (2-5 seconds per segment)
- Requires LLM deployment
- Less deterministic (responses vary)
- Harder to test/validate

**When to Use:**
- High-value content analysis
- Willing to trade speed for quality
- Already using Langflow/LLMs

---

### Strategy 5: Fine-Tuned Model ⭐⭐⭐⭐⭐ **Production-Grade**

**Complexity:** Very High (2-3 weeks)  
**Impact:** Very High  
**Cost:** Medium (training time/resources)

**Implementation:**
1. **Collect Training Data**
   - Manually label 500-1000 radio segments
   - Include diverse topics, tones, edge cases
   - Use domain experts for quality

2. **Fine-Tune BART or DistilBERT**
   ```python
   from transformers import Trainer, TrainingArguments
   from datasets import Dataset
   
   # Prepare dataset
   train_data = Dataset.from_dict({
       "text": [...],  # Segment transcripts
       "topic": [...],  # Ground truth topics
       "tone": [...]    # Ground truth tones
   })
   
   # Fine-tune model
   training_args = TrainingArguments(
       output_dir="./models/audio_classifier",
       num_train_epochs=3,
       per_device_train_batch_size=8
   )
   
   trainer = Trainer(
       model=model,
       args=training_args,
       train_dataset=train_data
   )
   
   trainer.train()
   ```

3. **Deploy Custom Model**
   ```python
   topic_classifier = pipeline(
       "text-classification",
       model="./models/audio_classifier"
   )
   ```

**Pros:**
- Best accuracy for your specific domain
- Fast inference (similar to current speed)
- Customized to radio/broadcast content
- Learns your specific categories

**Cons:**
- Requires labeled training data
- Time-intensive data collection
- Ongoing maintenance (retrain as content evolves)
- Expertise needed for tuning

---

### Strategy 6: Hybrid Approach ⭐⭐⭐ **Balanced**

**Complexity:** Medium (4-5 hours)  
**Impact:** High  
**Cost:** Free

**Combine multiple strategies:**

```python
def classify_segment_hybrid(text: str) -> dict:
    """
    Multi-stage classification for best of both worlds.
    """
    # Stage 1: Fast zero-shot for basic categories
    basic_classification = classify_segment(text)
    
    # Stage 2: Tag detection for warnings
    tags = detect_tags(text)
    
    # Stage 3: If topic is ambiguous (low confidence), use LLM
    topic_result = topic_classifier(text, TOPIC_LABELS)
    if topic_result["scores"][0] < 0.5:  # Low confidence
        llm_result = classify_segment_llm(text)
        return {
            **basic_classification,
            "topic": llm_result["primary_topic"],
            "secondary_topics": llm_result.get("secondary_topics", []),
            "tags": tags + llm_result.get("warnings", []),
            "confidence": "low",
            "classification_method": "llm"
        }
    
    # Stage 4: Return fast classification for clear cases
    return {
        **basic_classification,
        "tags": tags,
        "confidence": "high",
        "classification_method": "zero-shot"
    }
```

**Pros:**
- Fast for 80% of segments
- Accurate for tricky 20%
- Best balance of speed and quality
- Graceful degradation if LLM fails

**Cons:**
- More complex logic
- Variable response times
- Need to handle multiple code paths

---

## 📊 Comparison Matrix

| Strategy | Complexity | Speed | Accuracy | Cost | Best For |
|----------|-----------|-------|----------|------|----------|
| **Expand Labels** | ⭐ | Fast | Medium | Free | Quick improvement |
| **Multi-Label** | ⭐⭐ | Fast | High | Free | Nuanced content |
| **Content Tags** | ⭐⭐ | Medium | High | Free | Brand safety |
| **LLM-Based** | ⭐⭐⭐⭐ | Slow | Very High | Free/Paid | Quality > speed |
| **Fine-Tuned** | ⭐⭐⭐⭐⭐ | Fast | Very High | Medium | Production scale |
| **Hybrid** | ⭐⭐⭐ | Medium | Very High | Free | Balanced approach |

---

## 🎯 Recommended Implementation Plan

### Phase 1: Quick Wins (1-2 hours)
✅ **Expand label sets** to 12-14 topics and 10 tones  
✅ **Add confidence scores** to classification output  
✅ **Basic tag detection** for instrumental sections (already done)

### Phase 2: Essential Features (3-4 hours)
⭐ **Multi-label classification** with threshold  
⭐ **Profanity detection** using toxic-bert  
⭐ **Sentiment analysis** for content warnings

### Phase 3: Advanced (1-2 weeks)
💡 **Hybrid classification** with LLM fallback  
💡 **Fine-tuned model** for radio-specific content  
💡 **A/B testing** to compare strategies

---

## 🔧 Implementation Example: Multi-Label + Tags

**New `classifier.py`:**

```python
from transformers import pipeline

# Load models
topic_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
tone_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
profanity_classifier = pipeline("text-classification", model="unitary/toxic-bert")

# Expanded labels
TOPIC_LABELS = [
    "Health", "Entertainment", "Politics", "Technology", "Food", "Education",
    "Sports", "Business", "Science", "Travel", "Finance", "News"
]

TONE_LABELS = [
    "Informative", "Humorous", "Excited", "Neutral", "Controversial",
    "Sarcastic", "Serious", "Casual", "Professional", "Emotional"
]

def classify_segment(text: str, multi_label: bool = True, threshold: float = 0.3) -> dict:
    """
    Enhanced classification with multi-label support and tags.
    """
    topic_result = topic_classifier(text, TOPIC_LABELS)
    tone_result = tone_classifier(text, TONE_LABELS)
    
    # Detect tags
    tags = []
    
    # Profanity
    try:
        toxicity = profanity_classifier(text)[0]
        if toxicity["label"] == "toxic" and toxicity["score"] > 0.7:
            tags.append("profanity")
    except:
        pass
    
    # Instrumental detection
    if len(text.strip()) < 20:
        tags.append("instrumental")
    
    # Repetition (simple heuristic)
    words = text.split()
    if len(words) > 10 and len(set(words)) / len(words) < 0.4:
        tags.append("repetition")
    
    if multi_label:
        # Return all labels above threshold
        topics = [
            label for label, score in zip(topic_result["labels"], topic_result["scores"])
            if score >= threshold
        ]
        tones = [
            label for label, score in zip(tone_result["labels"], tone_result["scores"])
            if score >= threshold
        ]
        
        return {
            "topic": topics[0] if topics else "Unknown",
            "topics": topics,
            "topic_scores": dict(zip(topic_result["labels"][:3], topic_result["scores"][:3])),
            "tone": tones[0] if tones else "Unknown",
            "tones": tones,
            "tone_scores": dict(zip(tone_result["labels"][:3], tone_result["scores"][:3])),
            "tags": tags,
            "confidence": topic_result["scores"][0] if topic_result["scores"] else 0.0
        }
    else:
        # Single label (backward compatible)
        return {
            "topic": topic_result["labels"][0],
            "tone": tone_result["labels"][0],
            "tags": tags
        }
```

**Update Requirements:**
```bash
pip install unitary/toxic-bert
```

---

## 📈 Expected Improvements

### Current System
- **Accuracy:** ~70-80%
- **Speed:** ~300ms per segment
- **Coverage:** 6 topics × 5 tones = 30 combinations
- **Tags:** 0 (empty)

### After Improvements (Phase 1 + 2)
- **Accuracy:** ~85-90%
- **Speed:** ~500ms per segment (acceptable trade-off)
- **Coverage:** 12 topics × 10 tones = 120 combinations
- **Tags:** Profanity, sentiment, instrumental, repetition
- **Multi-label:** 2-3 labels per segment average

---

## 🧪 Testing Classification Changes

```python
# tests/test_classifier_enhanced.py
def test_multi_label_classification():
    text = "This recipe uses AI technology to optimize cooking"
    result = classify_segment(text, multi_label=True)
    
    # Should detect both Technology and Food
    assert "Technology" in result["topics"]
    assert "Food" in result["topics"]
    assert result["confidence"] > 0.3

def test_profanity_detection():
    text = "This damn product is shit"
    result = classify_segment(text)
    
    assert "profanity" in result["tags"]

def test_instrumental_detection():
    text = "🎵🎵🎵"  # Very short
    result = classify_segment(text)
    
    assert "instrumental" in result["tags"]
```

---

## 🔑 Key Takeaways

1. **Current system works** but is limited to single-label, no tags
2. **Multi-label classification** is the highest-impact quick win
3. **Content warning tags** are critical for brand safety (Advertiser persona)
4. **LLM-based classification** offers best quality but slower
5. **Hybrid approach** balances speed and accuracy
6. **Fine-tuning** is production-grade but requires investment

**Recommended:** Start with **Strategy 2 (Multi-Label)** + **Strategy 3 (Tags)** for immediate impact with minimal complexity.

---

## 📚 Related Documentation

- [ARCHITECTURE_PERSONAS_WORKERS.md](ARCHITECTURE_PERSONAS_WORKERS.md) - How personas use classifications
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current implementation status
- [TODO.md](TODO.md) - Planned improvements
