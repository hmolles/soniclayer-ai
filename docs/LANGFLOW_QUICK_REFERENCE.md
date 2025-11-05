# Langflow Quick Reference Card

## 🚀 Quick Start Commands

### Check Langflow Status
```bash
# Check if Langflow is running
curl -s http://localhost:7860/health
```

### Test a Chain (Manual)
```bash
# Test GenZ chain
curl -X POST http://localhost:7860/api/v1/run/genz_chain \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs" \
  -d '{
    "input_value": "{\"text\": \"This is so cool!\", \"topic\": \"Technology\", \"tone\": \"Excited\"}",
    "output_type": "chat",
    "input_type": "chat"
  }'

# Test Advertiser chain
curl -X POST http://localhost:7860/api/v1/run/advertiser_chain \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs" \
  -d '{
    "input_value": "{\"text\": \"Professional content.\", \"topic\": \"Business\", \"tone\": \"Informative\"}",
    "output_type": "chat",
    "input_type": "chat"
  }'
```

### Test Using Helper Script
```bash
source venv/bin/activate

# Check Langflow health
python scripts/test_langflow_chains.py health

# Test single chain
python scripts/test_langflow_chains.py test --chain genz_chain --segment humorous

# Validate all chains
python scripts/test_langflow_chains.py validate
```

---

## 📋 Persona Chain Checklist

When creating a new persona chain in Langflow:

- [ ] Flow created with name: `{persona}_chain` (e.g., `parents_chain`)
- [ ] Components added: Chat Input → Prompt → OpenAI → Chat Output
- [ ] Components connected in sequence
- [ ] OpenAI component configured:
  - [ ] Base URL: `http://host.docker.internal:1234/v1`
  - [ ] API Key: `lm-studio`
  - [ ] Model Name: (from LM Studio)
  - [ ] Temperature: `0.7`
  - [ ] Max Tokens: `500`
- [ ] Prompt includes:
  - [ ] Persona description
  - [ ] Segment variable: `{segment}`
  - [ ] JSON output format specified
  - [ ] Required fields: score, opinion, rationale, confidence, note
  - [ ] Example response shown
- [ ] Endpoint name set in Share → API Access → Input Schema
- [ ] Tested in Playground with sample input
- [ ] Flow saved
- [ ] Validated with test script

---

## 🎯 Required Response Format

Every persona chain MUST return this JSON structure:

```json
{
  "score": 4,
  "opinion": "Short reaction/opinion",
  "rationale": "2-3 sentences explaining the score",
  "confidence": 0.85,
  "note": "Brief comment or concern"
}
```

**Field Types:**
- `score`: **Integer** 1-5
- `opinion`: **String**
- `rationale`: **String**
- `confidence`: **Float** 0.0-1.0
- `note`: **String**

---

## ⚙️ Configuration Values

### LM Studio Connection (from Docker)
```
Base URL: http://host.docker.internal:1234/v1
API Key: lm-studio
```

### LM Studio Connection (native Langflow)
```
Base URL: http://localhost:1234/v1
API Key: lm-studio
```

### Langflow API
```
URL: http://localhost:7860
API Key: sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs
```

### Recommended OpenAI Component Settings
```
Temperature: 0.7
Max Tokens: 500
Top P: 1.0
Frequency Penalty: 0.0
Presence Penalty: 0.0
```

---

## 🔧 Troubleshooting Quick Fixes

### Flow returns empty response
```
✓ Check: Chat Input connected to Prompt
✓ Check: Prompt variable {segment} is used
✓ Check: All components connected in order
```

### "Connection refused" error
```
✓ Check: LM Studio running (http://localhost:1234)
✓ Check: Model loaded in LM Studio
✓ Check: Base URL is correct for Docker/native setup
```

### Invalid JSON response
```
✓ Add to prompt: "Return ONLY the JSON object, no other text"
✓ Add to prompt: "Do not use markdown code blocks"
✓ Increase Max Tokens if response is cut off
✓ Lower Temperature for more consistent output
```

### 401 Unauthorized
```
✓ Check: API key matches in curl command
✓ Check: x-api-key header is present
✓ Re-copy API key from Langflow settings
```

---

## 📊 Test Segments Reference

Use these for testing different persona reactions:

```json
// Humorous content
{
  "text": "So I was at the store buying oat milk, and the cashier goes 'that'll be $8' and I'm like WHAT?!",
  "topic": "Lifestyle",
  "tone": "Humorous"
}

// Formal/Academic
{
  "text": "Today we examine the socioeconomic implications of alternative dairy products.",
  "topic": "Academic",
  "tone": "Formal"
}

// Excited/Casual
{
  "text": "OMG you guys, the new iPhone just dropped and it's INSANE!",
  "topic": "Technology",
  "tone": "Excited"
}

// Controversial
{
  "text": "Let's talk politics - the latest scandal has everyone divided.",
  "topic": "Politics",
  "tone": "Serious"
}
```

---

## 🎓 Persona Characteristics Reference

### GenZ Persona
- **Age**: 18-27
- **Loves**: Humorous, excited, casual, pop culture, entertainment, tech
- **Hates**: Formal, academic, boring, repetitive
- **Scoring**: 5=fire 🔥, 1=awful
- **Style**: Slang, emojis OK

### Advertiser Persona
- **Role**: Brand safety analyst
- **Loves**: Professional tone, commercial topics, tech, food
- **Caution**: Controversial topics, strong opinions
- **Rejects**: Profanity, explicit content, divisive politics
- **Scoring**: 5=premium brand-safe, 1=unsuitable
- **Style**: Professional, analytical

### Template for New Personas
- **Define**: Age/role/background
- **Specify**: Topics they care about
- **List**: Preferences (love/hate)
- **Explain**: Scoring criteria
- **Set**: Communication style

---

## 📖 See Full Documentation

- **Setup Guide**: `docs/LANGFLOW_SETUP_GUIDE.md`
- **Test Script**: `scripts/test_langflow_chains.py`
- **API Docs**: https://docs.langflow.org/

---

**Last Updated**: 4 November 2025
