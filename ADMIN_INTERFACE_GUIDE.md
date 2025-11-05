# Admin Interface for Persona Management

## Overview
The SonicLayer AI dashboard now includes a **Persona Admin Panel** that allows you to add new audience personas dynamically without editing code files manually.

## Features

### ✅ Navigation Menu
- Located in the **top-right corner** of every page
- **📊 Dashboard** - Main audio analysis interface
- **⚙️ Admin** - Persona management panel

### ✅ Admin Panel Layout

**Left Column: Add New Persona**
- **Persona ID** - Unique identifier (lowercase, no spaces, e.g., `millennial`, `tech_enthusiast`)
- **Display Name** - Human-readable name shown in UI (e.g., "Millennial", "Tech Enthusiast")
- **Emoji** - Icon for visual identification (e.g., 🎯, 👴, 💻)
- **Description** - Brief description of the persona
- **Evaluation Prompt (JSON)** - The system and user prompts for Azure GPT evaluation

**Right Column: Existing Personas**
- Lists all currently registered personas
- Shows emoji, name, ID, and description

---

## How to Add a New Persona

### Step 1: Access Admin Panel
1. Navigate to your dashboard
2. Click **⚙️ Admin** in the top-right corner

### Step 2: Fill in Persona Details

#### Persona ID
- **Required field**
- Must be lowercase, alphanumeric (underscores allowed)
- No spaces
- Examples: `millennial`, `boomer`, `tech_enthusiast`
- This becomes the database key and worker file name

#### Display Name
- **Required field**
- Human-friendly name shown in the UI
- Examples: "Millennial", "Baby Boomer", "Tech Enthusiast"

#### Emoji
- Optional but recommended
- Single emoji character
- Used as visual identifier in persona cards
- Examples: 🎯, 👴, 💻, 🎓, 🏢

#### Description
- Optional
- Brief description of what this persona represents
- Examples: "Millennial content evaluator", "Tech industry professional"

#### Evaluation Prompt (JSON)
- **Required field**
- Must be valid JSON format
- Must contain two fields: `system` and `user_template`

**Example JSON Prompt:**
```json
{
  "system": "You are a millennial content evaluator. You value authentic, relatable content and appreciate references to 90s/2000s culture. You prefer casual tone over formal language.",
  "user_template": "Evaluate this audio segment from a millennial perspective:\n\nText: \"{text}\"\nTopic: {topic}\nTone: {tone}\n\nRate this segment on a scale of 1-5 (5 being best) and provide:\n1. score (1-5)\n2. opinion (brief reaction)\n3. rationale (why you gave this score)\n4. confidence (0.0-1.0, how confident you are in this rating)\n\nRespond ONLY with JSON:\n{{\"score\": <number>, \"opinion\": \"<text>\", \"rationale\": \"<text>\", \"confidence\": <number>}}"
}
```

### Step 3: Validate JSON
- As you type in the JSON prompt field, the system validates it in real-time
- ✅ **Valid JSON format** - Green checkmark appears
- ❌ **Invalid JSON** - Red error message shows the problem
- ⚠️ **Missing required fields** - Warning if `system` or `user_template` is missing

### Step 4: Submit
1. Click **Create Persona** button
2. System will:
   - Validate all inputs
   - Check persona ID format
   - Verify JSON structure
   - Create worker file automatically
   - Update configuration files
   - Show success message
3. Page refreshes to show the new persona in the "Existing Personas" list

---

## What Happens Behind the Scenes

When you create a new persona, the system automatically:

### 1. **Creates Worker File**
`app/workers/{persona_id}_worker.py` - Handles background processing for this persona

### 2. **Updates Backend Config**
`app/config/personas.py` - Adds persona to the registry with:
- ID
- Display name
- Emoji
- Worker module path
- Chain name
- Description

### 3. **Updates Dashboard Config**
`dashboard/personas_config.py` - Adds persona UI configuration

### 4. **Updates Langflow Client**
`app/services/langflow_client.py` - Adds the evaluation prompt to PERSONA_PROMPTS dictionary

### 5. **Automatic Integration**
- No code changes needed
- System automatically:
  - Enqueues the new persona's worker when audio is uploaded
  - Fetches feedback from Redis
  - Renders persona card in dashboard
  - Displays evaluations in real-time

---

## Validation Rules

### Persona ID
- ✅ Lowercase letters, numbers, underscores only
- ✅ Examples: `millennial`, `tech_guru`, `gen_alpha`
- ❌ Uppercase letters
- ❌ Spaces or special characters

### Display Name
- ✅ Any characters allowed
- ✅ Can include spaces and special characters
- Examples: "Gen Alpha", "Tech Guru 💻", "Millennial (18-35)"

### JSON Prompt
- ✅ Must be valid JSON
- ✅ Must contain `system` field
- ✅ Must contain `user_template` field
- ❌ Invalid JSON syntax
- ❌ Missing required fields

---

## Example: Creating a "Tech Enthusiast" Persona

**Persona ID:** `tech_enthusiast`

**Display Name:** `Tech Enthusiast`

**Emoji:** `💻`

**Description:** `Technology industry professional who values innovation and technical depth`

**Evaluation Prompt (JSON):**
```json
{
  "system": "You are a technology enthusiast evaluator. You love innovative ideas, technical depth, and cutting-edge topics. You prefer informative and excited tones over casual or humorous content.",
  "user_template": "Evaluate this audio segment from a tech enthusiast perspective:\n\nText: \"{text}\"\nTopic: {topic}\nTone: {tone}\n\nRate this segment on a scale of 1-5 (5 being best for tech content) and provide:\n1. score (1-5)\n2. opinion (brief tech-focused reaction)\n3. rationale (why you gave this score from a tech perspective)\n4. confidence (0.0-1.0)\n\nRespond ONLY with JSON:\n{{\"score\": <number>, \"opinion\": \"<text>\", \"rationale\": \"<text>\", \"confidence\": <number>}}"
}
```

After clicking **Create Persona**, the system:
1. Creates `app/workers/tech_enthusiast_worker.py`
2. Updates all config files
3. New persona is immediately available for all future audio uploads!

---

## Tips for Writing Good Prompts

### System Prompt
- Define the persona's identity and values
- Specify what they like/dislike
- Set their perspective and priorities

### User Template Prompt
- Use placeholders: `{text}`, `{topic}`, `{tone}`
- Be specific about the output format (JSON)
- Include all 4 fields: score, opinion, rationale, confidence
- Examples help guide the AI's responses

---

## Troubleshooting

### "Invalid JSON" Error
- Copy your JSON to a validator (jsonlint.com)
- Check for:
  - Missing commas
  - Unclosed quotes
  - Unescaped special characters
  - Missing braces

### "Persona ID must be lowercase" Error
- Remove uppercase letters
- Replace spaces with underscores
- Remove special characters except underscores

### Persona Not Showing in Dashboard
- Restart the backend and worker workflows
- Clear browser cache
- Re-upload a new audio file to test

---

## Architecture

The admin interface integrates seamlessly with the dynamic persona registry:

```
User fills form
     ↓
JSON validation (real-time)
     ↓
Click "Create Persona"
     ↓
Backend validation
     ↓
┌────────────────────────────────────────┐
│  Automatic File Updates (4 files)     │
├────────────────────────────────────────┤
│ 1. app/workers/{id}_worker.py         │
│ 2. app/config/personas.py              │
│ 3. dashboard/personas_config.py        │
│ 4. app/services/langflow_client.py    │
└────────────────────────────────────────┘
     ↓
Success! Persona ready for use
     ↓
Upload audio → All personas (including new one) automatically evaluate
```

---

## Benefits

✅ **No coding required** - Add personas through UI  
✅ **Real-time validation** - Instant feedback on JSON format  
✅ **Automatic integration** - System handles all technical details  
✅ **Scalable** - Add unlimited personas  
✅ **User-friendly** - Clean, intuitive interface  
✅ **Safe** - Validates all inputs before creating files  

---

## Security Considerations

- The admin panel is currently open to all users
- For production deployment, consider adding:
  - Authentication/login system
  - Role-based access control (admin-only)
  - Audit logging for persona creation
  - Backup/restore functionality

---

## Next Steps

1. **Create your first custom persona** using the admin interface
2. **Upload a new audio file** to see all personas evaluate it
3. **Iterate on prompts** by creating variations and comparing results
4. **Share successful personas** with your team

Happy persona creating! 🎯
