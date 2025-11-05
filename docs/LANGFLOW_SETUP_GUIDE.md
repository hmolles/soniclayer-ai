# Langflow Setup Guide - Creating Persona Evaluation Chains

**Date:** 4 November 2025  
**For:** SonicLayer AI MVP  
**Audience:** Non-technical users

---

## 📋 Overview

This guide will walk you through creating **persona evaluation chains** in Langflow. These chains analyze audio transcript segments and return scores from different audience perspectives (Gen Z, Advertisers, etc.).

**Time required:** 15-20 minutes per persona  
**Prerequisites:** 
- Langflow running at http://localhost:7860
- LM Studio running on localhost:1234 with a model loaded
- API key: `sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs`

---

## 🎯 What You'll Create

Two persona evaluation chains:
1. **GenZ Chain** - Evaluates content from Gen Z perspective
2. **Advertiser Chain** - Evaluates content for brand safety

Each chain receives a segment (transcript + topic + tone) and returns:
- `score`: 1-5 rating
- `opinion`: Short reaction
- `rationale`: Why that score
- `confidence`: 0.0-1.0 how sure
- `note`: Brief comment

---

## 🚀 Step-by-Step: Creating a Persona Chain

### Step 1: Access Langflow

1. Open your browser
2. Go to: **http://localhost:7860**
3. You should see the Langflow dashboard

![Langflow Dashboard](https://docs.langflow.org/assets/images/workspace-basic-prompting-61154cb9a883e7d5862f6c3d272add85.png)

---

### Step 2: Create a New Flow

1. Click **"New Flow"** or **"+ Create"** button
2. Choose **"Blank Flow"** (not a template)
3. Name it: `genz_chain` (all lowercase, no spaces)
4. Click **Create**

---

### Step 3: Add Required Components

You'll need 3 components for each chain:

#### A. Add Chat Input Component

1. In the left sidebar, search for: **"Chat Input"**
2. Drag it onto the canvas
3. Click on the component to configure:
   - **Name**: Leave as "Chat Input"
   - **Input Value**: Leave empty (will be provided via API)
4. This receives the segment JSON from our backend

#### B. Add Prompt Component

1. Search for: **"Prompt"**
2. Drag it onto the canvas
3. Click to configure:
   - **Template**: Paste the prompt text (see prompts below)
   - **Variables**: Should auto-detect `{input_value}` variable from Chat Input

#### C. Add OpenAI Model Component

1. Search for: **"OpenAI"** or **"Chat Model"**
2. Drag **"OpenAI"** component onto canvas
3. Click to configure:
   - **Base URL**: `http://host.docker.internal:1234/v1`
   - **API Key**: `lm-studio` (any non-empty value works)
   - **Model Name**: The model name shown in LM Studio (e.g., `qwen2.5-7b-instruct`)
   - **Temperature**: `0.7`
   - **Max Tokens**: `500`

   > **Note**: `host.docker.internal` allows the Docker container to access your host machine's localhost

#### D. Add Chat Output Component

1. Search for: **"Chat Output"**
2. Drag it onto the canvas
3. This returns the LLM's response

---

### Step 4: Connect Components

Click and drag to connect:

```
Chat Input (Message output) → Prompt (input_value variable)
Prompt (Prompt Message output) → OpenAI (Input)
OpenAI (Message output) → Chat Output (Input)
```

**How to connect:**
1. Click the **output handle** (right side circle) of Chat Input
2. Drag to the **input_value variable** circle on the Prompt component
3. Then connect Prompt's output to OpenAI's input
4. Finally connect OpenAI's output to Chat Output's input

Your flow should look like:
```
[Chat Input] → [Prompt] → [OpenAI Model] → [Chat Output]
```

---

### Step 5: Configure the Prompt

Click on the **Prompt** component and paste the appropriate prompt:

#### GenZ Persona Prompt

```
You are a Gen Z audience member (ages 18-27) evaluating a podcast segment. Analyze this segment and respond ONLY with valid JSON.

Segment:
{input_value}

Provide your evaluation as JSON with these exact fields:
- score: Integer 1-5 (1=awful, 5=fire 🔥)
- opinion: Short Gen Z reaction (use slang, emojis OK)
- rationale: Why you gave that score (2-3 sentences)
- confidence: Float 0.0-1.0 (how sure you are)
- note: One quick take

Preferences:
- LOVE: Humorous, excited, casual tones
- LOVE: Pop culture, entertainment, technology topics
- HATE: Formal, academic, boring stuff
- PENALIZE: Repetitive content

Example response (do NOT include the curly braces in field names):
score: 4
opinion: "lowkey funny ngl 😂"
rationale: "The humor hits different and the topic is actually interesting. Could use less repetition tho."
confidence: 0.85
note: "Would share with the group chat"

Return ONLY a valid JSON object with these exact fields, no other text.
```

#### Advertiser Persona Prompt

```
You are a brand safety analyst evaluating podcast content for advertising. Analyze this segment and respond ONLY with valid JSON.

Segment:
{input_value}

Provide your evaluation as JSON with these exact fields:
- score: Integer 1-5 (1=unsafe, 5=brand-safe)
- opinion: Professional assessment
- rationale: Brand safety analysis (2-3 sentences)
- confidence: Float 0.0-1.0 (certainty level)
- note: Key concern or approval

Brand Safety Criteria:
- APPROVE: Professional tone, commercial topics, technology, food content
- CAUTION: Controversial topics, strong opinions
- REJECT: Profanity, explicit content, divisive politics

Scoring:
- 5: Perfect for premium brands
- 4: Safe for most advertisers
- 3: Requires review
- 2: High risk
- 1: Unsuitable for advertising

Example response (do NOT include the curly braces in field names):
score: 4
opinion: "Suitable for consumer brands"
rationale: "Professional tone with broad appeal topic. No controversial elements detected. Minor concern about topic diversity."
confidence: 0.90
note: "⚠️ Monitor for brand alignment"

Return ONLY a valid JSON object with these exact fields, no other text.
```

---

### Step 6: Set the Endpoint Name

1. Click **"Share"** button (top right)
2. Select **"API Access"**
3. Click **"Input Schema"**
4. Find **"Endpoint Name"** field
5. Enter:
   - For GenZ: `genz_chain`
   - For Advertiser: `advertiser_chain`
6. Close the panel

This creates a clean API endpoint: `/api/v1/run/genz_chain`

---

### Step 7: Test the Flow

1. Click the **"Play"** button (▶️) at bottom right
2. In the **Chat** panel that opens:
3. Paste this test input:

```json
{
  "text": "Today we're talking about the new iPhone features. Pretty exciting stuff!",
  "topic": "Technology",
  "tone": "Excited"
}
```

4. Click **Send**
5. You should see a JSON response with score, opinion, etc.

**If it fails:**
- Check LM Studio is running with a model loaded
- Verify the Base URL in OpenAI component
- Check that the prompt asks for JSON output
- Try clicking the component and looking for error messages

---

### Step 8: Save and Deploy

1. Click **"Save"** (top right, floppy disk icon)
2. Your flow is now ready!
3. The API endpoint is: `http://localhost:7860/api/v1/run/genz_chain`

---

## 🔧 Testing Your Chain via API

Once created, test with curl:

```bash
curl -X POST http://localhost:7860/api/v1/run/genz_chain \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs" \
  -d '{
    "input_value": "{\"text\": \"This podcast segment is super boring and repetitive.\", \"topic\": \"Academic\", \"tone\": \"Formal\"}",
    "output_type": "chat",
    "input_type": "chat"
  }'
```

Expected response structure:
```json
{
  "outputs": [
    {
      "outputs": [
        {
          "results": {
            "message": {
              "text": "{\"score\": 2, \"opinion\": \"not it chief 😴\", ...}"
            }
          }
        }
      ]
    }
  ]
}
```

---

## 📝 Creating Additional Personas

To add a new persona (e.g., Parents, Regional, Academic):

### Quick Checklist:

1. **Create new flow** in Langflow
2. **Name it** (e.g., `parents_chain`)
3. **Add components**: Chat Input → Prompt → OpenAI → Chat Output
4. **Connect them** in sequence
5. **Write prompt** with persona characteristics:
   ```
   - Who they are (age, background)
   - What they care about
   - Topics they love/hate
   - Tone preferences
   - Scoring criteria
   ```
6. **Set endpoint name** in Share → API Access → Input Schema
7. **Test in playground**
8. **Save the flow**

### Prompt Template for New Personas:

```
You are a [PERSONA_DESCRIPTION] evaluating a podcast segment. Analyze this segment and respond ONLY with valid JSON.

Segment:
{input_value}

Provide your evaluation as JSON with these exact fields:
- score: Integer 1-5 (1=[WORST], 5=[BEST])
- opinion: [STYLE_DESCRIPTION] reaction
- rationale: Why you gave that score (2-3 sentences)
- confidence: Float 0.0-1.0 (how sure you are)
- note: [TYPE_OF_NOTE]

Preferences:
- LOVE: [Topics/tones they like]
- HATE: [Topics/tones they dislike]
- PENALIZE: [What reduces their score]

Example response (do NOT include the curly braces in field names):
score: 4
opinion: "[Example opinion]"
rationale: "[Example rationale]"
confidence: 0.85
note: "[Example note]"

Return ONLY a valid JSON object with these exact fields, no other text.
```

---

## 🔗 Connecting to SonicLayer Backend

Once your chains are created, update the backend to use them:

1. **Find the endpoint URL** from Langflow's Share → API Access
2. **Note the flow name** (e.g., `genz_chain`)
3. The backend will call: `http://localhost:7860/api/v1/run/{flow_name}`

Our workers automatically call these endpoints when processing audio segments!

---

## ⚠️ Troubleshooting

### "Model not found" error
**Solution:** Check LM Studio has a model loaded and note the exact model name

### "Connection refused"
**Solution:** 
- Verify LM Studio is running
- Check it's on port 1234
- Try `http://host.docker.internal:1234/v1` as Base URL
- If using native Langflow (not Docker), use `http://localhost:1234/v1`

### "Invalid JSON" in response
**Solution:**
- Update prompt to emphasize "Return ONLY the JSON object, no other text"
- Try adding "Do not include markdown code blocks" to prompt
- Increase Max Tokens if response is truncated

### Flow runs but returns empty
**Solution:**
- Check connections between components
- Verify Chat Input is connected to Prompt's `{segment}` variable
- Test with simpler input first

---

## 📊 Best Practices

1. **Test incrementally** - Test each component before connecting
2. **Use descriptive names** - Makes debugging easier
3. **Keep prompts clear** - Simpler = more reliable
4. **Monitor token usage** - Max Tokens affects cost/speed
5. **Version your flows** - Save copies before major changes
6. **Document your personas** - Write down what each one prioritizes

---

## 🎓 Example: Parents Persona

Here's a complete example for a third persona:

**Flow Name:** `parents_chain`

**Prompt:**
```
You are a parent (ages 35-50) evaluating podcast content for family-friendliness. Analyze this segment and respond ONLY with valid JSON.

Segment:
{input_value}

Provide your evaluation as JSON with these exact fields:
- score: Integer 1-5 (1=inappropriate, 5=family-friendly)
- opinion: Parental perspective
- rationale: Why you gave that score (2-3 sentences)
- confidence: Float 0.0-1.0 (how sure you are)
- note: Key concern or approval

Preferences:
- LOVE: Educational, informative, positive tone
- LOVE: Health, family, education topics
- HATE: Profanity, violence, inappropriate content
- PENALIZE: Overly casual or slang-heavy language

Example response (do NOT include the curly braces in field names):
score: 4
opinion: "Appropriate and informative"
rationale: "Good educational content with positive messaging. Language is clean and suitable for older children."
confidence: 0.88
note: "Would recommend for ages 12+"

Return ONLY a valid JSON object with these exact fields, no other text.
```

**Components:**
- Chat Input → Prompt → OpenAI (Base URL: `http://host.docker.internal:1234/v1`) → Chat Output

**Endpoint:** `http://localhost:7860/api/v1/run/parents_chain`

---

## 📞 Need Help?

- **Langflow docs**: https://docs.langflow.org/
- **Check backend logs**: Look for Langflow connection errors
- **Verify API key**: Must match in both Langflow and backend
- **Test LM Studio**: Try the API directly: `curl http://localhost:1234/v1/models`

---

**Next Steps:** After creating both chains, proceed to integration testing in the main system!
