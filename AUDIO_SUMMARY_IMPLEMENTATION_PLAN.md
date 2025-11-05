# Audio Summary Dashboard - Implementation Plan

## 🎯 Objective
Implement a **three-tier hybrid summary system** that displays aggregated persona ratings and reactions for each audio file across multiple views in the dashboard.

---

## 📋 Architecture Overview

### Three Display Locations (Hybrid Approach)
1. **File Browser Sidebar** - Mini summary cards with quick metrics
2. **Main Dashboard** - Collapsible summary panel above waveform
3. **New Summary Tab** - Full detailed analytics with distribution charts

---

## 🚨 Critical Implementation Rules

### DO:
- ✅ Follow existing codebase patterns (Redis keys, service layers, dynamic persona loops)
- ✅ Test each phase with the human operator before proceeding
- ✅ Use `get_all_personas()` for dynamic persona support (no hardcoding)
- ✅ Handle missing/incomplete data gracefully (some personas may not have processed yet)
- ✅ Maintain 24-hour TTL (86400 seconds) for all Redis caches
- ✅ Keep code modular and reusable across all three views
- ✅ Log errors but don't fail entire requests on partial data

### DON'T:
- ❌ Add features not specified in this plan (save improvements for later)
- ❌ Hardcode persona IDs ("genz", "advertiser", etc.)
- ❌ Break existing dashboard functionality
- ❌ Skip testing phases - verify with human after each phase
- ❌ Create new navigation patterns - follow existing tab structure
- ❌ Modify Redis key patterns for segment-level data

---

## 📐 Implementation Phases

---

## **PHASE 1: Backend Summary Endpoint** ⚙️

### Task 1.1: Create Summary Aggregation Service
**File:** `app/services/summary_aggregator.py` (NEW)

**Purpose:** Compute statistical aggregates from segment-level persona feedback

**Functions to implement:**

```python
def compute_score_distribution(scores: list) -> dict:
    """
    Count occurrences of each score (1-5)
    
    Args:
        scores: List of integer scores [3, 4, 2, 5, 4, ...]
    
    Returns:
        {"1": 2, "2": 5, "3": 8, "4": 2, "5": 1}
    """
    pass

def get_top_n_segments(scores: list, n: int = 3) -> list:
    """
    Return indices of top N highest-scoring segments
    
    Args:
        scores: [2, 4, 3, 5, 1, 5, 3]
        n: number of top segments to return
    
    Returns:
        [3, 5, 1]  # Segment indices with highest scores
    """
    pass

def get_worst_n_segments(scores: list, n: int = 2) -> list:
    """
    Return indices of worst N lowest-scoring segments
    
    Args:
        scores: [2, 4, 3, 5, 1, 5, 3]
        n: number of worst segments to return
    
    Returns:
        [4, 0]  # Segment indices with lowest scores
    """
    pass

def aggregate_persona_feedback(audio_id: str, persona_id: str, num_segments: int) -> dict:
    """
    Aggregate all segment-level feedback for a single persona
    
    Fetch from Redis: persona_feedback:{persona_id}:{audio_id}:{segment_id}
    for segment_id in range(0, num_segments)
    
    Returns:
        {
            "avg_score": 3.2,
            "score_distribution": {"1": 1, "2": 3, "3": 5, "4": 6, "5": 3},
            "avg_confidence": 0.75,
            "top_segments": [5, 12, 7],
            "worst_segments": [2, 9]
        }
    """
    pass
```

**Testing Checkpoint 1.1:**
- [ ] Run unit tests for each function
- [ ] Verify score distribution counts correctly
- [ ] Verify top/worst segment indices are accurate
- [ ] Test with edge cases (empty scores, single segment, all same scores)

---

### Task 1.2: Create Summary Route
**File:** `app/routes/summary.py` (NEW)

**Endpoint:** `GET /summary/{audio_id}`

**Purpose:** Aggregate all persona feedback for an audio file and cache result

**Implementation:**

```python
from fastapi import APIRouter, HTTPException
from app.services.cache import redis_conn
from app.config.personas import get_all_personas
from app.services.summary_aggregator import aggregate_persona_feedback
import json

router = APIRouter()

@router.get("/summary/{audio_id}")
async def get_audio_summary(audio_id: str):
    """
    Get aggregated summary statistics for all personas across all segments.
    
    Returns cached summary if available, otherwise computes from segment data.
    
    Response format:
    {
        "audio_id": "50f53153...",
        "num_segments": 18,
        "personas": {
            "genz": {
                "avg_score": 2.8,
                "score_distribution": {"1": 2, "2": 5, "3": 8, "4": 2, "5": 1},
                "avg_confidence": 0.72,
                "top_segments": [3, 7, 15],
                "worst_segments": [1, 9]
            },
            "advertiser": { ... }
        }
    }
    """
    # Step 1: Check cache
    cached = redis_conn.get(f"audio_summary:{audio_id}")
    if cached:
        return json.loads(cached)
    
    # Step 2: Verify transcript exists (determines num_segments)
    transcript_raw = redis_conn.get(f"transcript_segments:{audio_id}")
    if not transcript_raw:
        raise HTTPException(status_code=404, detail="Audio not found or not processed")
    
    transcript_segments = json.loads(transcript_raw)
    num_segments = len(transcript_segments)
    
    # Step 3: Build summary object
    summary = {
        "audio_id": audio_id,
        "num_segments": num_segments,
        "personas": {}
    }
    
    # Step 4: Loop through all registered personas
    personas = get_all_personas()
    for persona in personas:
        persona_id = persona["id"]
        
        # Aggregate this persona's feedback
        persona_summary = aggregate_persona_feedback(audio_id, persona_id, num_segments)
        
        # Only add if at least some feedback exists
        if persona_summary["avg_score"] > 0:
            summary["personas"][persona_id] = persona_summary
    
    # Step 5: Cache result for 24 hours
    redis_conn.set(f"audio_summary:{audio_id}", json.dumps(summary), ex=86400)
    
    return summary
```

**Testing Checkpoint 1.2:**
- [ ] Verify endpoint is registered in `app/main.py` (add router)
- [ ] Test with existing audio file: `curl http://localhost:8000/summary/{audio_id}`
- [ ] Verify response contains all active personas
- [ ] Verify Redis cache key is created: `audio_summary:{audio_id}`
- [ ] Test with non-existent audio_id (should 404)
- [ ] Human verification: Does response structure match expected format?

---

### Task 1.3: Register Summary Router
**File:** `app/main.py` (MODIFY)

**Change:** Add summary router to FastAPI app

```python
# Add import
from app.routes import summary

# Register router (add with other routers)
app.include_router(summary.router, tags=["summary"])
```

**Testing Checkpoint 1.3:**
- [ ] Restart backend: `uvicorn app.main:app --reload`
- [ ] Verify `/docs` shows new `/summary/{audio_id}` endpoint
- [ ] Test endpoint via Swagger UI
- [ ] Human verification: Can you access the summary endpoint successfully?

---

## **PHASE 2: File Browser Mini Cards** 🗂️

### Task 2.1: Update Audio Scanner to Fetch Summaries
**File:** `dashboard/utils/audio_scanner.py` (MODIFY)

**Purpose:** Enhance `get_all_audio_files()` to include summary data

**Current behavior:** Returns list of `{"audio_id": "...", "num_segments": N, ...}`

**New behavior:** Also fetch and include mini summary for each file

**Implementation guidance:**

```python
def get_all_audio_files():
    """
    Scan uploads/ folder and fetch summary stats for each audio file.
    
    Returns list with enhanced metadata:
    [
        {
            "audio_id": "50f53153...",
            "num_segments": 18,
            "file_size": "256 MB",
            "summary": {
                "genz": {"avg_score": 2.8, "emoji": "🔥"},
                "advertiser": {"avg_score": 4.2, "emoji": "💼"}
            }
        },
        ...
    ]
    """
    # Existing code to scan files...
    
    audio_files = []
    for file in Path("uploads").glob("*.wav"):
        audio_id = file.stem
        
        # Fetch summary from backend
        try:
            summary_response = requests.get(f"http://localhost:8000/summary/{audio_id}")
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                
                # Build mini summary (just avg scores + emojis)
                mini_summary = {}
                for persona_id, stats in summary_data.get("personas", {}).items():
                    # Find persona emoji from config
                    persona_config = next((p for p in get_all_personas() if p["id"] == persona_id), None)
                    if persona_config:
                        mini_summary[persona_id] = {
                            "avg_score": stats["avg_score"],
                            "emoji": persona_config["emoji"]
                        }
                
                audio_files.append({
                    "audio_id": audio_id,
                    "num_segments": summary_data["num_segments"],
                    "summary": mini_summary
                })
            else:
                # Summary not available yet
                audio_files.append({
                    "audio_id": audio_id,
                    "num_segments": 0,  # Unknown
                    "summary": {}
                })
        except Exception as e:
            # Fallback if backend unavailable
            audio_files.append({
                "audio_id": audio_id,
                "num_segments": 0,
                "summary": {}
            })
    
    return audio_files
```

**Testing Checkpoint 2.1:**
- [ ] Verify `get_all_audio_files()` returns summary data
- [ ] Test with multiple audio files
- [ ] Test graceful fallback when summary not available
- [ ] Human verification: Print output and verify structure

---

### Task 2.2: Update File Browser UI to Display Mini Cards
**File:** `dashboard/app.py` → `create_file_sidebar()` function (MODIFY)

**Purpose:** Display persona scores as colored emoji badges in file browser

**Current display:**
```
🎵 50f531... 
   18 segments
```

**New display:**
```
🎵 50f531... 
   18 segments
   🔥 2.8  💼 4.2  👨‍👩‍👧 3.5
```

**Implementation guidance:**

Modify the file item creation loop in `create_file_sidebar()`:

```python
# Inside the loop creating file_items
for i, audio in enumerate(audio_files):
    short_id = audio["audio_id"][:12] + "..."
    
    # Build persona score badges
    score_badges = []
    if audio.get("summary"):
        for persona_id, mini_stats in audio["summary"].items():
            emoji = mini_stats["emoji"]
            avg_score = mini_stats["avg_score"]
            
            # Color-code based on score
            color = "#10b981" if avg_score >= 4 else "#f59e0b" if avg_score >= 3 else "#ef4444"
            
            badge = html.Span([
                html.Span(emoji, style={"marginRight": "2px"}),
                html.Span(f"{avg_score}", style={"fontWeight": "600", "color": color})
            ], style={
                "display": "inline-block",
                "marginRight": "8px",
                "fontSize": "11px"
            })
            score_badges.append(badge)
    
    # Build file item with badges
    item = html.Button([
        html.Span("🎵", style={"fontSize": "20px", "marginRight": "8px"}),
        html.Div([
            html.Div(short_id, style={...}),
            html.Div(f"{audio['num_segments']} segments", style={...}),
            # Add score badges row
            html.Div(score_badges, style={"marginTop": "4px"}) if score_badges else None
        ], style={...})
    ], ...)
```

**Testing Checkpoint 2.2:**
- [ ] Restart dashboard: `python dashboard/app.py`
- [ ] Verify file browser shows emoji score badges
- [ ] Verify colors change based on score (green ≥4, amber ≥3, red <3)
- [ ] Test with files that have no summary (should show gracefully)
- [ ] Human verification: Does the file browser look correct? Are scores displaying?

---

## **PHASE 3: Main Dashboard Collapsible Panel** 📊

### Task 3.1: Create Collapsible Summary Component
**File:** `dashboard/components/summary_panel.py` (NEW)

**Purpose:** Reusable component for rendering persona summary with distribution

**Functions to implement:**

```python
from dash import html, dcc
import plotly.graph_objects as go

def get_score_color(score):
    """Return color based on score (1-5 scale)"""
    if score >= 4:
        return "#10b981"  # Green
    elif score >= 3:
        return "#f59e0b"  # Amber
    else:
        return "#ef4444"  # Red

def create_distribution_bar(distribution: dict) -> html.Div:
    """
    Create simple horizontal bar showing score distribution
    
    Args:
        distribution: {"1": 2, "2": 5, "3": 8, "4": 2, "5": 1}
    
    Returns:
        Dash HTML component with colored segments
    """
    total = sum(distribution.values())
    if total == 0:
        return html.Div("No data")
    
    segments = []
    for score in ["1", "2", "3", "4", "5"]:
        count = distribution.get(score, 0)
        percentage = (count / total) * 100
        
        if percentage > 0:
            color = get_score_color(int(score))
            segments.append(html.Div(
                f"{score}: {count}",
                style={
                    "width": f"{percentage}%",
                    "backgroundColor": color,
                    "color": "white",
                    "textAlign": "center",
                    "fontSize": "11px",
                    "padding": "4px 0",
                    "display": "inline-block"
                }
            ))
    
    return html.Div(segments, style={
        "display": "flex",
        "width": "100%",
        "borderRadius": "4px",
        "overflow": "hidden",
        "marginBottom": "8px"
    })

def render_persona_summary_card(persona_id: str, persona_name: str, emoji: str, stats: dict) -> html.Div:
    """
    Render single persona's summary card
    
    Args:
        persona_id: "genz"
        persona_name: "Gen Z"
        emoji: "🔥"
        stats: {
            "avg_score": 2.8,
            "score_distribution": {"1": 2, "2": 5, "3": 8, "4": 2, "5": 1},
            "avg_confidence": 0.72,
            "top_segments": [3, 7, 15],
            "worst_segments": [1, 9]
        }
    
    Returns:
        Dash HTML card component
    """
    avg_score = stats.get("avg_score", 0)
    score_color = get_score_color(avg_score)
    
    return html.Div([
        # Header
        html.Div([
            html.Span(emoji, style={"fontSize": "18px", "marginRight": "6px"}),
            html.Span(persona_name, style={"fontWeight": "bold", "fontSize": "14px"}),
            html.Span(
                f"{avg_score}/5",
                style={
                    "float": "right",
                    "backgroundColor": score_color,
                    "color": "white",
                    "padding": "3px 10px",
                    "borderRadius": "12px",
                    "fontSize": "12px",
                    "fontWeight": "600"
                }
            )
        ], style={"marginBottom": "10px"}),
        
        # Distribution bar
        create_distribution_bar(stats.get("score_distribution", {})),
        
        # Top segments
        html.Div([
            html.Strong("⭐ Best: ", style={"fontSize": "11px"}),
            html.Span(
                f"Segments {', '.join(map(str, stats.get('top_segments', [])))}",
                style={"fontSize": "11px", "color": "#374151"}
            )
        ], style={"marginBottom": "4px"}),
        
        # Worst segments
        html.Div([
            html.Strong("⚠️ Worst: ", style={"fontSize": "11px"}),
            html.Span(
                f"Segments {', '.join(map(str, stats.get('worst_segments', [])))}",
                style={"fontSize": "11px", "color": "#6b7280"}
            )
        ])
        
    ], style={
        "padding": "12px",
        "backgroundColor": "#f9fafb",
        "borderRadius": "6px",
        "border": f"1px solid {score_color}",
        "marginBottom": "8px"
    })

def render_collapsible_summary(summary_data: dict, is_expanded: bool = True) -> html.Div:
    """
    Main collapsible summary panel
    
    Args:
        summary_data: Full summary response from /summary/{audio_id}
        is_expanded: Whether panel starts open or collapsed
    
    Returns:
        Dash HTML component with collapse button
    """
    if not summary_data or not summary_data.get("personas"):
        return html.Div(
            "⏳ Summary not available yet - processing...",
            style={
                "padding": "16px",
                "backgroundColor": "#fef3c7",
                "borderRadius": "8px",
                "color": "#92400e",
                "marginBottom": "20px",
                "textAlign": "center",
                "fontSize": "14px"
            }
        )
    
    # Build persona cards
    from dashboard.personas_config import get_all_personas
    persona_cards = []
    
    for persona in get_all_personas():
        persona_id = persona["id"]
        stats = summary_data["personas"].get(persona_id)
        
        if stats:  # Only show if this persona has data
            card = render_persona_summary_card(
                persona_id,
                persona["display_name"],
                persona["emoji"],
                stats
            )
            persona_cards.append(card)
    
    # Summary header
    num_segments = summary_data.get("num_segments", 0)
    num_personas = len(summary_data.get("personas", {}))
    
    return html.Div([
        # Toggle button
        html.Button(
            f"{'▼' if is_expanded else '▶'} Audio Summary ({num_segments} segments, {num_personas} personas)",
            id="toggle-summary-btn",
            n_clicks=0,
            style={
                "width": "100%",
                "padding": "12px",
                "backgroundColor": "#3b82f6",
                "color": "white",
                "border": "none",
                "borderRadius": "8px",
                "cursor": "pointer",
                "fontSize": "14px",
                "fontWeight": "600",
                "marginBottom": "12px",
                "textAlign": "left"
            }
        ),
        
        # Collapsible content
        html.Div(
            persona_cards,
            id="summary-content",
            style={
                "display": "block" if is_expanded else "none",
                "padding": "12px",
                "backgroundColor": "#ffffff",
                "borderRadius": "8px",
                "border": "1px solid #e5e7eb",
                "marginBottom": "20px"
            }
        )
    ])
```

**Testing Checkpoint 3.1:**
- [ ] Test component in isolation (create test script if needed)
- [ ] Verify distribution bar percentages add to 100%
- [ ] Verify colors match score ranges
- [ ] Human verification: Does the component render correctly?

---

### Task 3.2: Integrate Summary Panel in Main Dashboard
**File:** `dashboard/app.py` (MODIFY)

**Location:** Insert summary panel above waveform in main content area

**Steps:**

1. **Import the component:**
```python
from components.summary_panel import render_collapsible_summary
```

2. **Add Store for summary data:**
```python
# In app.layout, add near other dcc.Store components:
dcc.Store(id='summary-data-store', data=None),
dcc.Store(id='summary-expanded', data=True),  # Tracks collapse state
```

3. **Insert panel in layout:**
Find the section where waveform is rendered (around line 180-200), add summary panel above it:

```python
# Main content column (right side)
html.Div([
    # Header
    html.H1("SonicLayer AI Dashboard", style={...}),
    
    # **INSERT HERE: Summary Panel**
    html.Div(id="summary-panel-container", children=[
        html.Div("Select an audio file to view summary", style={
            "padding": "20px",
            "color": "#6b7280",
            "textAlign": "center"
        })
    ]),
    
    # Existing waveform
    html.Div(id="waveform-container", ...),
    ...
])
```

4. **Add callback to fetch and render summary:**
```python
# Callback: Fetch summary when audio changes
@app.callback(
    Output('summary-data-store', 'data'),
    Input('current-audio-id', 'data'),
    prevent_initial_call=True
)
def fetch_summary_data(audio_id):
    """Fetch summary from backend when audio changes"""
    if not audio_id:
        raise PreventUpdate
    
    try:
        response = requests.get(f"http://localhost:8000/summary/{audio_id}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching summary: {e}")
    
    return None

# Callback: Render summary panel
@app.callback(
    Output('summary-panel-container', 'children'),
    Input('summary-data-store', 'data'),
    Input('summary-expanded', 'data'),
    prevent_initial_call=False
)
def update_summary_panel(summary_data, is_expanded):
    """Render collapsible summary panel"""
    if summary_data is None:
        return html.Div("Select an audio file to view summary", style={
            "padding": "20px",
            "color": "#6b7280",
            "textAlign": "center",
            "backgroundColor": "#f9fafb",
            "borderRadius": "8px",
            "marginBottom": "20px"
        })
    
    return render_collapsible_summary(summary_data, is_expanded)

# Callback: Toggle collapse state
@app.callback(
    Output('summary-expanded', 'data'),
    Output('summary-content', 'style'),
    Input('toggle-summary-btn', 'n_clicks'),
    State('summary-expanded', 'data'),
    prevent_initial_call=True
)
def toggle_summary_collapse(n_clicks, current_state):
    """Toggle summary panel expand/collapse"""
    new_state = not current_state
    
    return new_state, {
        "display": "block" if new_state else "none",
        "padding": "12px",
        "backgroundColor": "#ffffff",
        "borderRadius": "8px",
        "border": "1px solid #e5e7eb",
        "marginBottom": "20px"
    }
```

**Testing Checkpoint 3.2:**
- [ ] Restart dashboard
- [ ] Select audio file from browser
- [ ] Verify summary panel appears above waveform
- [ ] Verify all personas shown with correct stats
- [ ] Test collapse/expand button functionality
- [ ] Verify colors and layout match design
- [ ] Human verification: Does the summary panel look correct? Can you collapse/expand it?

---

## **PHASE 4: New Summary Tab** 📈

### Task 4.1: Add Summary Tab to Navigation
**File:** `dashboard/components/navigation.py` (if exists) OR `dashboard/app.py` (MODIFY)

**Purpose:** Add third tab alongside existing "Dashboard" and "Admin"

**Current tabs:**
- Dashboard
- Admin

**New structure:**
- Dashboard
- Summary ← NEW
- Admin

**Implementation guidance:**

If navigation is in separate component file, modify that. Otherwise, modify `dashboard/app.py` layout section where tabs are defined.

Look for the navigation section (likely near top of layout), add new tab:

```python
# Navigation tabs
html.Div([
    html.Button("Dashboard", id="tab-dashboard", ...),
    html.Button("Summary", id="tab-summary", n_clicks=0, style={
        "padding": "10px 20px",
        "marginRight": "8px",
        "border": "1px solid #e5e7eb",
        "borderRadius": "6px",
        "backgroundColor": "#ffffff",
        "cursor": "pointer"
    }),
    html.Button("Admin", id="tab-admin", ...),
], style={...})
```

**Testing Checkpoint 4.1:**
- [ ] Verify Summary tab appears in navigation
- [ ] Tab should not do anything yet (not wired up)
- [ ] Human verification: Can you see the Summary tab?

---

### Task 4.2: Create Summary Page Container
**File:** `dashboard/app.py` (MODIFY)

**Purpose:** Add hidden container that shows when Summary tab is active

**Implementation guidance:**

Add new container div in main layout (similar to how admin modal is hidden):

```python
# In app.layout, after main dashboard content:

# Summary Tab Page (hidden by default)
html.Div([
    html.Div([
        html.H2("📊 Audio Summary Analytics", style={"marginBottom": "20px"}),
        html.Div(id="summary-tab-content", children=[
            html.Div("Select an audio file to view detailed analytics", style={
                "padding": "40px",
                "textAlign": "center",
                "color": "#6b7280"
            })
        ])
    ], style={
        "padding": "30px",
        "maxWidth": "1200px",
        "margin": "0 auto"
    })
], id="summary-tab-page", style={"display": "none"})
```

**Testing Checkpoint 4.2:**
- [ ] Container exists but is hidden
- [ ] No visual changes yet
- [ ] Human verification: No errors in browser console?

---

### Task 4.3: Add Tab Switching Logic
**File:** `dashboard/app.py` (MODIFY)

**Purpose:** Show/hide appropriate containers when tabs are clicked

**Implementation guidance:**

Add callback to handle tab switching:

```python
@app.callback(
    Output('main-dashboard-content', 'style'),  # Existing dashboard
    Output('summary-tab-page', 'style'),         # New summary page
    Output('admin-modal', 'style'),              # Existing admin modal
    Input('tab-dashboard', 'n_clicks'),
    Input('tab-summary', 'n_clicks'),
    Input('tab-admin', 'n_clicks'),
    Input('admin-close-btn', 'n_clicks'),
    prevent_initial_call=False
)
def switch_tabs(dash_clicks, summary_clicks, admin_clicks, admin_close):
    """Switch between Dashboard, Summary, and Admin tabs"""
    ctx = callback_context
    
    # Default: show dashboard
    if not ctx.triggered:
        return {"display": "block"}, {"display": "none"}, {"display": "none"}
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'tab-dashboard':
        return {"display": "block"}, {"display": "none"}, {"display": "none"}
    elif button_id == 'tab-summary':
        return {"display": "none"}, {"display": "block"}, {"display": "none"}
    elif button_id == 'tab-admin':
        return {"display": "none"}, {"display": "none"}, {"display": "block"}
    elif button_id == 'admin-close-btn':
        return {"display": "block"}, {"display": "none"}, {"display": "none"}
    
    # Default
    return {"display": "block"}, {"display": "none"}, {"display": "none"}
```

**Note:** You may need to wrap existing dashboard content in a container div with id `main-dashboard-content` if it doesn't already have one.

**Testing Checkpoint 4.3:**
- [ ] Click Dashboard tab → main dashboard shows
- [ ] Click Summary tab → summary page shows, dashboard hides
- [ ] Click Admin tab → admin modal shows
- [ ] File browser should remain visible on all tabs
- [ ] Human verification: Can you switch between tabs correctly?

---

### Task 4.4: Create Detailed Summary View Component
**File:** `dashboard/components/summary_panel.py` (MODIFY - add new function)

**Purpose:** Full-page detailed view with charts and statistics

**Add function:**

```python
def render_detailed_summary(summary_data: dict) -> html.Div:
    """
    Render full-page summary view with detailed charts
    
    Args:
        summary_data: Full summary response from /summary/{audio_id}
    
    Returns:
        Comprehensive dashboard with multiple visualizations
    """
    if not summary_data or not summary_data.get("personas"):
        return html.Div(
            "⏳ No summary data available. Select an audio file and ensure it has been processed.",
            style={
                "padding": "60px",
                "textAlign": "center",
                "color": "#6b7280",
                "fontSize": "16px"
            }
        )
    
    from dashboard.personas_config import get_all_personas
    
    num_segments = summary_data.get("num_segments", 0)
    num_personas = len(summary_data.get("personas", {}))
    
    # Build persona detail cards (larger than collapsible version)
    persona_sections = []
    
    for persona in get_all_personas():
        persona_id = persona["id"]
        stats = summary_data["personas"].get(persona_id)
        
        if not stats:
            continue
        
        avg_score = stats.get("avg_score", 0)
        score_color = get_score_color(avg_score)
        distribution = stats.get("score_distribution", {})
        
        # Create distribution chart (simple bar chart)
        fig = go.Figure(data=[
            go.Bar(
                x=list(distribution.keys()),
                y=list(distribution.values()),
                marker_color=[get_score_color(int(k)) for k in distribution.keys()],
                text=list(distribution.values()),
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title=f"Score Distribution",
            xaxis_title="Score",
            yaxis_title="Count",
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False
        )
        
        persona_section = html.Div([
            # Header
            html.Div([
                html.Span(persona["emoji"], style={"fontSize": "32px", "marginRight": "12px"}),
                html.Span(persona["display_name"], style={
                    "fontSize": "24px",
                    "fontWeight": "bold",
                    "color": "#111827"
                }),
                html.Span(
                    f"{avg_score}/5",
                    style={
                        "float": "right",
                        "backgroundColor": score_color,
                        "color": "white",
                        "padding": "8px 20px",
                        "borderRadius": "20px",
                        "fontSize": "18px",
                        "fontWeight": "bold"
                    }
                )
            ], style={"marginBottom": "20px", "paddingBottom": "12px", "borderBottom": "2px solid #e5e7eb"}),
            
            # Stats grid
            html.Div([
                # Avg confidence
                html.Div([
                    html.Div("Avg Confidence", style={"fontSize": "12px", "color": "#6b7280", "marginBottom": "4px"}),
                    html.Div(f"{int(stats.get('avg_confidence', 0) * 100)}%", style={
                        "fontSize": "24px",
                        "fontWeight": "bold",
                        "color": "#111827"
                    })
                ], style={"flex": "1", "padding": "12px", "backgroundColor": "#f9fafb", "borderRadius": "6px"}),
                
                # Top segments
                html.Div([
                    html.Div("Best Segments", style={"fontSize": "12px", "color": "#6b7280", "marginBottom": "4px"}),
                    html.Div(
                        ", ".join(map(str, stats.get("top_segments", []))),
                        style={"fontSize": "18px", "fontWeight": "600", "color": "#10b981"}
                    )
                ], style={"flex": "1", "padding": "12px", "backgroundColor": "#f9fafb", "borderRadius": "6px", "marginLeft": "12px"}),
                
                # Worst segments
                html.Div([
                    html.Div("Worst Segments", style={"fontSize": "12px", "color": "#6b7280", "marginBottom": "4px"}),
                    html.Div(
                        ", ".join(map(str, stats.get("worst_segments", []))),
                        style={"fontSize": "18px", "fontWeight": "600", "color": "#ef4444"}
                    )
                ], style={"flex": "1", "padding": "12px", "backgroundColor": "#f9fafb", "borderRadius": "6px", "marginLeft": "12px"})
                
            ], style={"display": "flex", "marginBottom": "20px"}),
            
            # Distribution chart
            dcc.Graph(figure=fig, config={"displayModeBar": False})
            
        ], style={
            "padding": "24px",
            "backgroundColor": "#ffffff",
            "borderRadius": "12px",
            "border": f"2px solid {score_color}",
            "marginBottom": "24px",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
        })
        
        persona_sections.append(persona_section)
    
    # Overall summary header
    header = html.Div([
        html.H3(f"Audio: {summary_data['audio_id'][:16]}...", style={"marginBottom": "8px"}),
        html.Div([
            html.Span(f"📊 {num_segments} Segments", style={"marginRight": "20px", "fontSize": "14px"}),
            html.Span(f"👥 {num_personas} Personas Evaluated", style={"fontSize": "14px"})
        ], style={"color": "#6b7280", "marginBottom": "30px"})
    ])
    
    return html.Div([
        header,
        *persona_sections
    ])
```

**Testing Checkpoint 4.4:**
- [ ] Test component renders with mock data
- [ ] Verify charts display correctly
- [ ] Human verification: Does the detailed view look good?

---

### Task 4.5: Wire Summary Tab Content
**File:** `dashboard/app.py` (MODIFY)

**Purpose:** Populate summary tab with detailed view when audio selected

**Add callback:**

```python
from components.summary_panel import render_detailed_summary

@app.callback(
    Output('summary-tab-content', 'children'),
    Input('summary-data-store', 'data'),
    prevent_initial_call=False
)
def update_summary_tab(summary_data):
    """Render detailed summary in Summary tab"""
    return render_detailed_summary(summary_data)
```

**Testing Checkpoint 4.5:**
- [ ] Select audio file from browser
- [ ] Click Summary tab
- [ ] Verify detailed view shows all personas
- [ ] Verify charts render correctly
- [ ] Test with different audio files
- [ ] Human verification: Does the summary tab show complete data? Are charts accurate?

---

## **FINAL TESTING & VERIFICATION** ✅

### Complete System Test
- [ ] **File Browser**: Shows emoji score badges for all audio files
- [ ] **Main Dashboard**: Collapsible summary panel appears above waveform
- [ ] **Summary Tab**: Full detailed analytics with charts
- [ ] **Tab Switching**: Seamless navigation between Dashboard/Summary/Admin
- [ ] **Data Consistency**: Same scores appear across all three views
- [ ] **Loading States**: Graceful handling when summary not ready
- [ ] **Multiple Files**: Switch between audio files, verify summaries update

### Edge Cases to Test
- [ ] Audio file with no persona feedback yet (should show "processing" message)
- [ ] Audio file with partial persona feedback (some personas done, others pending)
- [ ] Empty uploads folder (file browser should handle gracefully)
- [ ] Backend offline (dashboard should not crash)
- [ ] Very long audio (many segments) - does summary handle well?
- [ ] Single segment audio - does distribution work?

### Performance Checks
- [ ] Summary endpoint responds within 1-2 seconds
- [ ] Dashboard doesn't lag when switching between files
- [ ] Redis cache is being used (check logs for cache hits)
- [ ] No memory leaks or console errors

### Human Operator Final Verification
- [ ] **Visual Design**: Does everything look polished and professional?
- [ ] **User Experience**: Is it intuitive to navigate?
- [ ] **Data Accuracy**: Do scores make sense compared to segment-level data?
- [ ] **Completeness**: Are all three views implemented per the hybrid approach?
- [ ] **No Extra Features**: Confirm only specified features were added

---

## 📝 Documentation Updates

After implementation, update these files:

### `README.md`
Add section about summary features:
```markdown
## Summary Analytics

SonicLayer AI provides three levels of summary analytics:

1. **File Browser**: Quick persona scores at a glance
2. **Dashboard Panel**: Collapsible summary above waveform
3. **Summary Tab**: Detailed analytics with distribution charts

Access summary endpoint: `GET /summary/{audio_id}`
```

### `QUICK_START.md`
Add instructions for viewing summaries:
```markdown
### Viewing Audio Summaries

1. Upload and process an audio file
2. Check file browser for quick persona scores
3. Click file to see collapsible summary in dashboard
4. Click "Summary" tab for detailed analytics
```

---

## 🚫 Out of Scope (Do Not Implement)

These improvements are planned for later phases:

- ❌ Sentiment trend detection (improving/declining/stable)
- ❌ Persona comparison/divergence analytics
- ❌ Heatmap visualizations
- ❌ Word cloud for topics
- ❌ Multi-file comparison
- ❌ Export to JSON/CSV
- ❌ Click-to-segment navigation from summary
- ❌ Filtering segments by score threshold
- ❌ Consensus segment detection
- ❌ Alert system for low scores
- ❌ Pre-computation in worker queue
- ❌ Streaming/incremental updates

**If you're tempted to add these features, STOP and consult with the human operator first.**

---

## 🐛 Troubleshooting Guide

### Summary endpoint returns 404
- Verify audio_id exists in `uploads/` folder
- Check Redis for `transcript_segments:{audio_id}` key
- Ensure audio has been processed through `/evaluate/` endpoint

### Summary shows empty personas object
- Check if persona workers have completed
- Verify Redis keys: `persona_feedback:{persona_id}:{audio_id}:{segment_id}`
- Check worker logs for errors

### File browser not showing scores
- Verify backend is running on port 8000
- Check network tab in browser dev tools for failed requests
- Verify `audio_scanner.py` is making correct API calls

### Dashboard summary panel not appearing
- Check that `summary-data-store` is being populated
- Verify callback is triggered when audio changes
- Check browser console for React/Dash errors

### Summary tab is blank
- Verify tab switching callback is working
- Check that `summary-tab-content` id matches in callback
- Verify `render_detailed_summary()` is imported correctly

---

## 📋 Checklist Summary

Copy this checklist and mark items as you complete them:

**Phase 1: Backend**
- [ ] 1.1: Create summary_aggregator.py service
- [ ] 1.2: Create summary.py route
- [ ] 1.3: Register summary router in main.py

**Phase 2: File Browser**
- [ ] 2.1: Update audio_scanner.py to fetch summaries
- [ ] 2.2: Update file browser UI with score badges

**Phase 3: Dashboard Panel**
- [ ] 3.1: Create summary_panel.py component
- [ ] 3.2: Integrate collapsible panel in dashboard

**Phase 4: Summary Tab**
- [ ] 4.1: Add Summary tab to navigation
- [ ] 4.2: Create summary page container
- [ ] 4.3: Add tab switching logic
- [ ] 4.4: Create detailed summary view
- [ ] 4.5: Wire summary tab content

**Final Testing**
- [ ] Complete system test
- [ ] Edge case testing
- [ ] Performance checks
- [ ] Human operator approval

---

## 🎯 Success Criteria

Implementation is complete when:

1. ✅ Summary endpoint returns correct aggregated data
2. ✅ File browser shows persona score badges
3. ✅ Dashboard has collapsible summary panel above waveform
4. ✅ Summary tab shows detailed analytics with charts
5. ✅ All three views show consistent data
6. ✅ System handles edge cases gracefully
7. ✅ No console errors or performance issues
8. ✅ Human operator approves all visual designs
9. ✅ Only specified features implemented (no extras)
10. ✅ Code follows existing patterns and conventions

---

**REMEMBER:** Test with human operator after each phase before proceeding to the next!
