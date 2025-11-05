# Azure AI Content Safety Integration - Implementation Guide

## Overview
This guide provides step-by-step instructions to integrate Azure AI Content Safety API into the SonicLayer AI platform to automatically flag audio files containing sensitive content (violence, hate speech, sexual content, self-harm references).

---

## Prerequisites

1. **Azure Subscription** with access to create Cognitive Services resources
2. **Existing SonicLayer AI installation** with the following working:
   - FastAPI backend (`app/`)
   - Redis cache
   - Audio upload and transcription pipeline
3. **Python packages** (will be added to requirements.txt)

---

## Phase 1: Azure Resource Setup

### Step 1.1: Create Azure Content Safety Resource

1. Log in to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"**
3. Search for **"Content Safety"**
4. Click **"Create"** and fill in:
   - **Subscription:** Your Azure subscription
   - **Resource Group:** Create new or use existing (e.g., `soniclayer-resources`)
   - **Region:** Choose nearest region (e.g., `East US`)
   - **Name:** `soniclayer-content-safety`
   - **Pricing Tier:** `Free F0` (for testing) or `Standard S0` (for production)
5. Click **"Review + create"** → **"Create"**
6. Wait for deployment (1-2 minutes)

### Step 1.2: Get API Credentials

1. Go to your new **Content Safety** resource
2. In left menu, click **"Keys and Endpoint"**
3. Copy these values (you'll need them later):
   - **KEY 1** (or KEY 2)
   - **Endpoint** (e.g., `https://soniclayer-content-safety.cognitiveservices.azure.com/`)

---

## Phase 2: Environment Configuration

### Step 2.1: Add Environment Variables

Edit your `.env` file (create if it doesn't exist in project root):

```bash
# Azure Content Safety API
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_KEY=your_api_key_here

# Content moderation threshold (severity 0-7, recommend 4)
CONTENT_SAFETY_THRESHOLD=4
```

**Replace:**
- `your-resource-name` with your actual resource name
- `your_api_key_here` with KEY 1 from Azure Portal

### Step 2.2: Update Requirements

Add to `requirements.txt`:

```txt
azure-ai-contentsafety==1.0.0
azure-core>=1.30.0
```

Install the new dependencies:

```bash
pip install azure-ai-contentsafety azure-core
```

---

## Phase 3: Create Content Safety Service

### Step 3.1: Create Service Module

Create new file: `app/services/azure_content_safety.py`

```python
"""
Azure AI Content Safety integration for SonicLayer AI.

This module provides content moderation using Azure's Content Safety API
to detect hate speech, violence, sexual content, and self-harm references
in audio transcripts.
"""

from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.exceptions import HttpResponseError
import os
import logging

logger = logging.getLogger(__name__)

# Configuration
ENDPOINT = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
API_KEY = os.getenv("AZURE_CONTENT_SAFETY_KEY")
SEVERITY_THRESHOLD = int(os.getenv("CONTENT_SAFETY_THRESHOLD", "4"))


def get_content_safety_client():
    """Initialize and return Azure Content Safety client."""
    if not ENDPOINT or not API_KEY:
        raise ValueError(
            "Azure Content Safety credentials not configured. "
            "Set AZURE_CONTENT_SAFETY_ENDPOINT and AZURE_CONTENT_SAFETY_KEY environment variables."
        )
    
    return ContentSafetyClient(ENDPOINT, AzureKeyCredential(API_KEY))


def check_content_safety(text: str, threshold: int = None) -> dict:
    """
    Analyze text for content safety issues using Azure AI Content Safety.
    
    Args:
        text: Text to analyze (audio transcript)
        threshold: Custom severity threshold (0-7). If None, uses SEVERITY_THRESHOLD env var.
                  Severity levels:
                  0-1: Safe
                  2-3: Low risk
                  4-5: Medium risk
                  6-7: High risk
    
    Returns:
        {
            "flagged": bool,  # True if any category exceeds threshold
            "categories": {
                "hate": {"severity": int, "flagged": bool},
                "sexual": {"severity": int, "flagged": bool},
                "violence": {"severity": int, "flagged": bool},
                "self_harm": {"severity": int, "flagged": bool}
            },
            "overall_severity": int,  # Highest severity across all categories
            "summary": str  # Human-readable summary
        }
    
    Raises:
        ValueError: If credentials not configured
        HttpResponseError: If Azure API call fails
    """
    if threshold is None:
        threshold = SEVERITY_THRESHOLD
    
    # Truncate text if too long (Azure has 10k character limit)
    if len(text) > 10000:
        logger.warning(f"Text exceeds 10k characters ({len(text)}), truncating...")
        text = text[:10000]
    
    try:
        client = get_content_safety_client()
        
        # Create analysis request
        request = AnalyzeTextOptions(text=text)
        
        # Call Azure API
        response = client.analyze_text(request)
        
        # Parse results
        categories = {}
        max_severity = 0
        flagged = False
        flagged_categories = []
        
        # Process each category
        for category_result in response.categories_analysis:
            category_name = category_result.category.lower().replace(" ", "_")
            severity = category_result.severity
            is_flagged = severity >= threshold
            
            categories[category_name] = {
                "severity": severity,
                "flagged": is_flagged
            }
            
            if is_flagged:
                flagged = True
                flagged_categories.append(category_name)
            
            max_severity = max(max_severity, severity)
        
        # Generate summary
        if flagged:
            summary = f"Content flagged for: {', '.join(flagged_categories)}"
        else:
            summary = "No content warnings"
        
        logger.info(
            f"Content safety check complete: flagged={flagged}, "
            f"max_severity={max_severity}, categories={flagged_categories}"
        )
        
        return {
            "flagged": flagged,
            "categories": categories,
            "overall_severity": max_severity,
            "summary": summary
        }
    
    except HttpResponseError as e:
        logger.error(f"Azure Content Safety API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Content safety check failed: {e}")
        raise


def get_severity_label(severity: int) -> str:
    """
    Convert numeric severity (0-7) to human-readable label.
    
    Args:
        severity: Severity level from Azure (0-7)
    
    Returns:
        Label string: "Safe", "Low", "Medium", or "High"
    """
    if severity <= 1:
        return "Safe"
    elif severity <= 3:
        return "Low"
    elif severity <= 5:
        return "Medium"
    else:
        return "High"


def format_warning_message(content_check: dict) -> str:
    """
    Format content check results into a user-friendly warning message.
    
    Args:
        content_check: Result from check_content_safety()
    
    Returns:
        Formatted warning string
    """
    if not content_check.get("flagged"):
        return "No content warnings"
    
    categories = content_check.get("categories", {})
    warnings = []
    
    for cat_name, cat_data in categories.items():
        if cat_data.get("flagged"):
            severity = cat_data.get("severity", 0)
            label = get_severity_label(severity)
            warnings.append(f"{cat_name.replace('_', ' ').title()} ({label})")
    
    return "⚠️ " + ", ".join(warnings)
```

### Step 3.2: Test the Service (Optional)

Create test file: `test_content_safety.py` (in project root)

```python
"""Test Azure Content Safety integration."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from services.azure_content_safety import check_content_safety

# Test cases
test_texts = {
    "safe": "This is a podcast about technology and innovation.",
    "violence": "The fight scene was brutal, with graphic descriptions of injuries.",
    "hate": "This content contains discriminatory language and hate speech.",
    "self_harm": "Discussion of self-harm and suicidal ideation."
}

print("Testing Azure Content Safety API...\n")

for label, text in test_texts.items():
    print(f"Testing: {label}")
    print(f"Text: {text}")
    
    try:
        result = check_content_safety(text)
        print(f"Result: {result['summary']}")
        print(f"Flagged: {result['flagged']}")
        print(f"Severity: {result['overall_severity']}")
        print(f"Categories: {result['categories']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("-" * 80)
```

Run the test:
```bash
python test_content_safety.py
```

Expected output should show flagged categories and severity levels.

---

## Phase 4: Integrate into Upload Pipeline

### Step 4.1: Update Evaluation Route

Edit `app/routes/evaluate.py`:

**Add import at top of file (around line 10):**

```python
from app.services.azure_content_safety import check_content_safety, format_warning_message
```

**Add content safety check after transcription (around line 90, after transcript_segments is created):**

Find this section:
```python
# Step 2: Classify segments (topic + tone)
classifier_results = []
```

**Add BEFORE the classification step:**

```python
# Step 1.5: Content Safety Check (NEW)
# Combine all transcript text for safety analysis
full_transcript = " ".join([seg.get("text", "") for seg in transcript_segments])

try:
    logger.info(f"Running content safety check on {len(full_transcript)} characters...")
    content_warnings = check_content_safety(full_transcript)
    
    # Store in Redis (24h TTL)
    redis_conn.set(
        f"content_warnings:{audio_id}",
        json.dumps(content_warnings),
        ex=86400
    )
    
    logger.info(
        f"Content safety check complete: "
        f"flagged={content_warnings['flagged']}, "
        f"severity={content_warnings['overall_severity']}"
    )
    
    # Optional: Log detailed warning if flagged
    if content_warnings['flagged']:
        logger.warning(f"Content warning for {audio_id}: {content_warnings['summary']}")
    
except Exception as e:
    logger.error(f"Content safety check failed for {audio_id}: {str(e)}")
    # Store empty result so we don't retry on every request
    redis_conn.set(
        f"content_warnings:{audio_id}",
        json.dumps({"flagged": False, "error": str(e)}),
        ex=86400
    )
```

---

## Phase 5: Add to File Browser

### Step 5.1: Update Audio Scanner

Edit `dashboard/utils/audio_scanner.py`:

**Add import at top:**
```python
import json
```

**Find the section where audio_files.append() is called (around line 100), update to:**

```python
            # Fetch content warnings if available
            import sys
            from pathlib import Path as SysPath
            sys.path.insert(0, str(SysPath(__file__).parent.parent.parent / "app"))
            from services.cache import redis_conn
            
            warnings_data = redis_conn.get(f"content_warnings:{audio_id}")
            has_warnings = False
            warning_categories = []
            
            if warnings_data:
                try:
                    warnings = json.loads(warnings_data)
                    has_warnings = warnings.get("flagged", False)
                    if has_warnings:
                        warning_categories = [
                            cat for cat, data in warnings.get("categories", {}).items()
                            if data.get("flagged")
                        ]
                except:
                    pass
            
            audio_files.append({
                "audio_id": audio_id,
                "filename": file_path.name,
                "display_name": display_name,
                "file_size_mb": file_size_mb,
                "upload_date": upload_date,
                "num_segments": num_segments,
                "summary": summary,
                "has_warnings": has_warnings,  # NEW
                "warning_categories": warning_categories  # NEW
            })
```

### Step 5.2: Update File Browser UI

Edit `dashboard/components/file_browser.py`:

**Find the section that creates file cards (around line 37), add warning badge:**

```python
            for audio in audio_files:
                # Use display_name (original filename) if available, otherwise shorten audio_id
                display_text = audio.get("display_name", audio["audio_id"][:16] + "...")
                
                # Add warning icon if flagged (NEW)
                warning_badge = None
                if audio.get("has_warnings"):
                    warning_badge = html.Span("⚠️", style={
                        "fontSize": "16px",
                        "color": "#ef4444",
                        "marginLeft": "6px"
                    }, title="Content warning: " + ", ".join(audio.get("warning_categories", [])))
                
                card = html.Div([
```

**Then update the display_text Div to include the badge:**

Find:
```python
                    html.Div(display_text, style={
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "color": "#111827",
```

Replace with:
```python
                    html.Div([
                        html.Span(display_text),
                        warning_badge  # NEW
                    ], style={
                        "fontSize": "16px",
                        "fontWeight": "600",
                        "color": "#111827",
```

---

## Phase 6: Display in Dashboard

### Step 6.1: Add Warning to Waveform Title

Edit `dashboard/app.py`:

**In the `load_audio_file` callback (around line 1115), after fetching display_name:**

```python
    # Get display name (original filename if available)
    display_name = get_audio_display_name(audio_id)
    
    # Check for content warnings (NEW)
    warnings_data = redis_conn.get(f"content_warnings:{audio_id}")
    if warnings_data:
        try:
            warnings = json.loads(warnings_data)
            if warnings.get("flagged"):
                display_name = f"⚠️ {display_name}"
        except:
            pass
```

### Step 6.2: Add Warning Panel in Metadata

Edit `dashboard/components/metadata_panel.py`:

**At the top of `render_metadata_panel` function, add:**

```python
def render_metadata_panel(segment: dict) -> html.Div:
    """Render the metadata panel for a segment."""
    
    # Check for content warnings (NEW)
    audio_id = segment.get("audio_id")  # You may need to pass this from parent
    warning_section = None
    
    if audio_id:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))
        from services.cache import redis_conn
        import json
        
        warnings_data = redis_conn.get(f"content_warnings:{audio_id}")
        if warnings_data:
            try:
                warnings = json.loads(warnings_data)
                if warnings.get("flagged"):
                    warning_section = html.Div([
                        html.Div("⚠️ Content Warning", style={
                            "fontSize": "12px",
                            "fontWeight": "600",
                            "color": "#ef4444",
                            "marginBottom": "6px"
                        }),
                        html.Div(warnings.get("summary", ""), style={
                            "fontSize": "11px",
                            "color": "#6b7280",
                            "padding": "8px",
                            "backgroundColor": "#fef2f2",
                            "borderLeft": "3px solid #ef4444",
                            "borderRadius": "4px"
                        })
                    ], style={"marginBottom": "16px"})
            except:
                pass
    
    # Rest of existing function...
```

---

## Phase 7: Testing

### Step 7.1: Test Full Pipeline

1. **Upload a test audio file** with safe content:
   ```bash
   curl -X POST http://localhost:8000/evaluate/ \
     -F "file=@test_audio_safe.wav"
   ```

2. **Check Redis for warnings:**
   ```bash
   redis-cli
   GET content_warnings:YOUR_AUDIO_ID_HERE
   ```

3. **Verify in dashboard:**
   - Open dashboard: `http://localhost:5000`
   - Check file browser for warning badges
   - Load file and check for warning in waveform title

### Step 7.2: Test with Flagged Content

Create a test audio with simulated violent content:
- Record or generate audio saying: "This podcast discusses graphic violence and explicit content"
- Upload via curl or dashboard
- Verify warning badge appears

---

## Phase 8: Configuration & Tuning

### Step 8.1: Adjust Sensitivity Threshold

The `CONTENT_SAFETY_THRESHOLD` env var controls sensitivity:
- **0-1:** Very strict (flags almost everything)
- **2-3:** Strict (conservative, more false positives)
- **4:** **Recommended default** (balanced)
- **5-6:** Lenient (fewer warnings)
- **7:** Very lenient (only extreme cases)

Edit `.env` to adjust:
```bash
CONTENT_SAFETY_THRESHOLD=4  # Change this value
```

### Step 8.2: Per-Category Thresholds (Advanced)

To set different thresholds per category, modify `check_content_safety()`:

```python
# In azure_content_safety.py
CATEGORY_THRESHOLDS = {
    "hate": 3,      # More strict for hate speech
    "sexual": 5,    # More lenient for sexual content
    "violence": 4,  # Default
    "self_harm": 3  # More strict for self-harm
}

# Then in the loop:
threshold_for_cat = CATEGORY_THRESHOLDS.get(category_name, threshold)
is_flagged = severity >= threshold_for_cat
```

---

## Troubleshooting

### Issue: "Azure Content Safety credentials not configured"
**Solution:** Verify `.env` file has correct values and is in project root

### Issue: "HttpResponseError: 401 Unauthorized"
**Solution:** Check that API key is correct and resource is active in Azure Portal

### Issue: "Text exceeds 10k characters"
**Solution:** Text is automatically truncated; consider analyzing per-segment instead

### Issue: Warnings not showing in dashboard
**Solution:** 
1. Check Redis: `redis-cli GET content_warnings:AUDIO_ID`
2. Verify service is called in `evaluate.py`
3. Check browser console for JavaScript errors

---

## Cost Estimation

Azure Content Safety pricing (as of 2025):
- **Free tier:** 5,000 transactions/month
- **Standard tier:** $1.00 per 1,000 transactions

For typical podcast (30 min, ~5,000 words):
- 1 analysis per upload
- ~50 uploads/day = $1.50/month

---

## Next Steps

1. **Implement all phases above in order**
2. **Test with real audio files**
3. **Fine-tune threshold based on your content**
4. **Optional:** Add per-segment warnings (analyze each segment individually)
5. **Optional:** Create "Content Safety" persona for detailed explanations

---

## Support Resources

- [Azure Content Safety Docs](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/)
- [Python SDK Reference](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-contentsafety-readme)
- [SonicLayer AI Architecture](./ARCHITECTURE_PERSONAS_WORKERS.md)
