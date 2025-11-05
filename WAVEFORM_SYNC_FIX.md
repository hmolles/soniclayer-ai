# Waveform Synchronization Bug Fix

## Problem Summary
The waveform highlighting and segment metadata updating during audio playback were broken after implementing the audio summary features (Phases 3-4).

## Root Causes Identified

### 1. **Callback Race Condition**
**Location:** `dashboard/app.py` lines 1384-1424

**Problem:**
- `fetch_summary_data` callback had `prevent_initial_call=False`
- `update_summary_panel` callback had `prevent_initial_call=False`
- These callbacks were firing **on initial render** and **on every audio change**
- This created race conditions with the critical waveform sync callbacks:
  - `load_audio_file` (line 989)
  - `auto_update_playback` (line 1304)

**Impact:**
- Multiple callbacks competing to update `waveform-graph` and `segment-metadata` simultaneously
- HTTP request to `/summary/{audio_id}` blocking the event loop during waveform initialization
- Playback sync interval getting starved of updates

**Fix:**
Changed both callbacks to use `prevent_initial_call=True`:
```python
@app.callback(
    Output('summary-data-store', 'data'),
    Input('current-audio-id', 'data'),
    prevent_initial_call=True  # ← Changed from False
)
def fetch_summary_data(audio_id):
    ...

@app.callback(
    Output('summary-panel-container', 'children'),
    Input('summary-data-store', 'data'),
    State('summary-collapsed', 'data'),
    prevent_initial_call=True  # ← Changed from False
)
def update_summary_panel(summary_data, is_collapsed):
    ...
```

### 2. **Nested Component Update Conflict**
**Location:** `dashboard/app.py` lines 1428-1463 (original implementation)

**Problem:**
- `toggle_summary_collapse` callback was trying to update:
  - `summary-collapse-content` (Output)
  - `summary-collapse-toggle` (Output)
- These components are **children** of `summary-panel-container`
- `update_summary_panel` callback **already outputs to** `summary-panel-container`
- **Dash does not allow callbacks to directly update components nested inside other callback outputs**

**Impact:**
- Callback resolution errors
- Component ID conflicts
- Updates to nested components being lost when parent re-renders
- Potential callback chain breakage affecting other components

**Fix:**
Replaced the problematic callback with a simpler version that re-renders the entire panel:
```python
@app.callback(
    Output('summary-collapsed', 'data'),
    Output('summary-panel-container', 'children', allow_duplicate=True),
    Input('summary-collapse-toggle', 'n_clicks'),
    State('summary-collapsed', 'data'),
    State('summary-data-store', 'data'),
    prevent_initial_call=True
)
def toggle_summary_collapse(n_clicks, is_collapsed, summary_data):
    """Toggle the collapse state and re-render the summary panel."""
    if summary_data is None:
        raise PreventUpdate
    
    new_collapsed = not is_collapsed
    personas = get_all_personas()
    new_panel = render_collapsible_summary(personas, summary_data, is_expanded=not new_collapsed)
    
    return new_collapsed, new_panel
```

## Callback Execution Flow (After Fix)

### On App Startup:
1. `app.layout` renders with default components
2. `load_audio_file` fires if default_audio_id exists
3. Summary callbacks **do not fire** (prevent_initial_call=True)
4. Waveform initializes cleanly

### On Audio Selection:
1. `selected-audio-store` updates
2. `load_audio_file` fires → updates:
   - `current-audio-id` ← **This triggers fetch_summary_data**
   - `waveform-graph`
   - `segment-metadata`
   - Other stores
3. `fetch_summary_data` fires (triggered by `current-audio-id` change) → fetches summary from backend
4. `update_summary_panel` fires (triggered by `summary-data-store` change) → renders summary panel
5. No race condition because summary fetch happens **after** waveform initialization

### During Playback:
1. `playback-sync` interval fires every 1000ms
2. `auto_update_playback` callback fires → updates:
   - `waveform-graph` (highlight current segment)
   - `segment-metadata` (show current segment details)
3. Summary callbacks **do not interfere** (only fire on audio change)

## Lessons Learned

### Dash Callback Rules:
1. **Never set `prevent_initial_call=False` for callbacks that fetch external data** - it creates race conditions on app startup
2. **Never try to update components nested inside other callback outputs** - use `allow_duplicate=True` and re-render the parent
3. **Always consider callback timing** - callbacks triggered by the same Input will queue, potentially blocking critical updates
4. **Use `allow_duplicate=True`** when multiple callbacks need to update the same Output at different times

### Safe Patterns:
- ✅ One callback per top-level component Output
- ✅ Re-render entire parent components instead of updating nested children
- ✅ Use `prevent_initial_call=True` for data-fetching callbacks
- ✅ Use clientside callbacks for purely visual interactions (toggles, animations)

### Dangerous Patterns:
- ❌ Multiple callbacks updating nested components within a dynamic parent
- ❌ `prevent_initial_call=False` for HTTP-dependent callbacks
- ❌ Long-running operations (HTTP requests) in callbacks without proper queuing
- ❌ Circular callback dependencies

## Testing Checklist

After applying this fix, verify:
- [ ] Waveform displays correctly on audio load
- [ ] Waveform highlights segments during playback
- [ ] Segment metadata updates during playback
- [ ] Summary panel renders above waveform
- [ ] Summary panel toggle (expand/collapse) works
- [ ] Summary tab displays data
- [ ] No console errors in browser developer tools
- [ ] No callback errors in backend logs

## Files Modified
1. `dashboard/app.py`
   - Line 1389: Changed `prevent_initial_call=False` → `True` for `fetch_summary_data`
   - Line 1413: Changed `prevent_initial_call=False` → `True` for `update_summary_panel`
   - Lines 1428-1463: Replaced `toggle_summary_collapse` callback with simplified version
