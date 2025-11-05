# Waveform Cursor & Metadata Update Issue - Analysis & Fix

**Date:** November 5, 2025  
**Issue:** Waveform cursor not showing, metadata/persona evaluations not updating during playback  
**Status:** 🔴 BROKEN - Likely due to UI changes

---

## 🔍 My Understanding of Previous Issue & Resolution

### Original Problem (Before)
The waveform cursor and metadata panel were not updating smoothly during audio playback. The issue was:

1. **Interval was too fast (250ms)** - caused jittery updates and performance issues
2. **No amplitude caching** - recalculated min/max on every update (~18+ calculations per second)
3. **Callback conflicts** - multiple callbacks trying to update the same outputs
4. **Clientside callback syntax issues** - using `const`/`let` caused browser compatibility problems

### Previous Solution
1. **Increased interval to 1000ms (1 second)** - smoother, less CPU-intensive
2. **Added amplitude caching** - cached `amp_min` and `amp_max` in waveform-data-store
3. **Simplified clientside callbacks** - removed `const`/`let`, used simpler inline JavaScript
4. **Proper callback chain** - Interval → clientside → store → server callback → UI update

---

## 🔴 Current Problem

Based on the code inspection, the **architecture is still intact**, but something is preventing the callbacks from executing. Let me diagnose:

### Architecture Check ✅

1. **Interval Component:** ✅ Present at line 374
   ```python
   dcc.Interval(id="playback-sync", interval=1000, n_intervals=0)
   ```

2. **Clientside Callback (Time Reader):** ✅ Present at lines 1347-1362
   ```javascript
   function(n_intervals) {
       const audioElement = document.getElementById('audio-player');
       if (audioElement && audioElement.currentTime !== undefined && !isNaN(audioElement.currentTime)) {
           return audioElement.currentTime;
       }
       return window.dash_clientside.no_update;
   }
   ```

3. **Server Callback (Update UI):** ✅ Present at lines 1389-1458
   ```python
   def auto_update_playback(current_time, segments, waveform_data, user_clicked, audio_id):
       # Updates waveform cursor and metadata
   ```

4. **Data Flow Chain:** ✅ Correct
   ```
   playback-sync (interval) 
   → clientside callback reads audio.currentTime
   → current-time-store updated
   → auto_update_playback triggered
   → waveform-graph + segment-metadata updated
   ```

---

## 🐛 Potential Root Causes

### Hypothesis 1: Audio Player Element Not Found ⚠️ MOST LIKELY
The clientside callback looks for `document.getElementById('audio-player')`, but recent UI changes may have:
- Changed the element ID
- Wrapped it in a way that delays rendering
- Made it conditionally rendered

**Evidence from code:**
```python
# Line 285-287
html.Div(id="audio-player-container", children=html.Div([
    html.Audio(
        id="audio-player",  # ← Should exist, but might not be rendered yet
```

The audio player is inside a container that gets replaced by the `load_audio_file` callback. If this callback isn't firing, or if it's firing but not rendering the audio element correctly, the clientside callback will fail silently.

---

### Hypothesis 2: Dark Mode CSS/JavaScript Interference ⚠️ POSSIBLE
The aggressive dark mode JavaScript we just analyzed does this:
```javascript
observer = new MutationObserver(function(mutations) {
    // Runs on EVERY DOM change
    if (hasNewNodes) {
        setTimeout(() => {
            swapInlineColors(isDark);
        }, 100);
    }
});
```

This could be:
- Causing the callbacks to lose references
- Interfering with Dash's internal DOM updates
- Creating race conditions when elements are re-rendered

---

### Hypothesis 3: Callback Order/Timing Issue ⚠️ POSSIBLE
The `load_audio_file` callback (line 1071) outputs to `audio-player-container`, which creates the audio element. If this happens AFTER the clientside callback tries to find the element, it will fail.

**Callback execution order:**
1. Page loads → `playback-sync` starts firing
2. Clientside callback tries to find `audio-player` → **NOT FOUND YET**
3. User clicks file → `load_audio_file` creates `audio-player`
4. But clientside callback already failed → never retries

---

### Hypothesis 4: Console Errors Being Silently Swallowed 🔍
The clientside callback has no error logging. If it's failing, we wouldn't know.

---

## 🔬 Diagnostic Steps

### Step 1: Check Browser Console
Open browser DevTools (F12) and look for:
```
Uncaught TypeError: Cannot read properties of null (reading 'currentTime')
```

Or any errors related to `audio-player` or Dash callbacks.

---

### Step 2: Verify Audio Element Exists
In browser console, run:
```javascript
console.log(document.getElementById('audio-player'));
```

**Expected:** Should return the `<audio>` element  
**If null:** Element doesn't exist or has wrong ID

---

### Step 3: Check if Interval is Firing
In browser console, run:
```javascript
// Check if interval component exists
document.querySelector('[id="playback-sync"]');
```

---

### Step 4: Check Server Logs
When audio plays, you should see:
```
[AUTO_UPDATE] time=1.234, user_clicked=False, has_segments=True, has_waveform=True
[AUTO_UPDATE] Rendering waveform at time 1.23, amp_min=-0.456, amp_max=0.789
```

**If you don't see these logs:** The callback chain is broken somewhere.

---

## 🛠️ Fix Plan

### Fix 1: Add Error Handling to Clientside Callback ⚡ IMMEDIATE

**Problem:** Clientside callback fails silently if audio element not found.

**Solution:** Add logging and defensive checks.

**File:** `/home/runner/workspace/dashboard/app.py`

**Location:** Lines 1347-1362 (clientside callback)

**Replace this:**
```javascript
app.clientside_callback(
    """
    function(n_intervals) {
        const audioElement = document.getElementById('audio-player');
        
        if (audioElement && audioElement.currentTime !== undefined && !isNaN(audioElement.currentTime)) {
            return audioElement.currentTime;
        }
        
        return window.dash_clientside.no_update;
    }
    """,
```

**With this:**
```javascript
app.clientside_callback(
    """
    function(n_intervals) {
        try {
            const audioElement = document.getElementById('audio-player');
            
            if (!audioElement) {
                // Log only once per second to avoid spam
                if (n_intervals % 5 === 0) {
                    console.log('[Playback Sync] Audio element not found (interval:', n_intervals, ')');
                }
                return window.dash_clientside.no_update;
            }
            
            if (audioElement.currentTime !== undefined && !isNaN(audioElement.currentTime)) {
                // Log every 5 seconds for debugging
                if (n_intervals % 5 === 0) {
                    console.log('[Playback Sync] Time:', audioElement.currentTime.toFixed(2), 's');
                }
                return audioElement.currentTime;
            }
            
            return window.dash_clientside.no_update;
        } catch (error) {
            console.error('[Playback Sync] Error:', error);
            return window.dash_clientside.no_update;
        }
    }
    """,
```

**Benefits:**
- Logs when audio element is missing (helps diagnose)
- Logs current time every 5 seconds (confirms it's working)
- Catches and logs any errors
- Doesn't spam console (only logs every 5 intervals)

---

### Fix 2: Ensure Audio Element Renders Before Interval Starts ⚡ IMPORTANT

**Problem:** Interval might start before audio element is created.

**Solution:** Make sure `load_audio_file` callback fires on initial load.

**File:** `/home/runner/workspace/dashboard/app.py`

**Location:** Lines 376-378 (Store initialization)

**Check current code:**
```python
dcc.Store(id='current-audio-id', data=default_audio_id),
```

**If `default_audio_id` is None, the audio never loads.**

**Verify the logic:** Lines 1088-1096 in `load_audio_file`:
```python
if not audio_id:
    audio_id = default_audio_id

if not audio_id:
    return (
        None,
        [],
        ...
    )
```

**If no default_audio_id, no audio loads → no audio element → clientside callback fails.**

**Fix:** Make sure when user clicks a file, the audio loads properly. Check the file browser click callback.

---

### Fix 3: Add Diagnostic Logging to Server Callback 🔍

**Problem:** Don't know if server callback is being triggered.

**Solution:** Already has good logging! But let's enhance it.

**File:** `/home/runner/workspace/dashboard/app.py`

**Location:** Line 1402 (start of auto_update_playback)

**The logging is already good:**
```python
print(f"[AUTO_UPDATE] time={current_time}, user_clicked={user_clicked}, has_segments={bool(segments)}, has_waveform={bool(waveform_data)}")
```

**But add this at the END of the function (line ~1458):**
```python
    if active_segment:
        print(f"[AUTO_UPDATE] Active segment: {active_segment.get('start')}-{active_segment.get('end')}")
        print(f"[AUTO_UPDATE] ✅ Updated waveform cursor to {current_time:.2f}s and metadata")  # ADD THIS
    
    # ... rest of code
```

---

### Fix 4: Disable Dark Mode Observer During Dash Updates 🔧 ADVANCED

**Problem:** Dark mode mutation observer might interfere with Dash callbacks.

**Solution:** Temporarily disable observer during Dash updates.

**File:** `/home/runner/workspace/dashboard/assets/dark-mode.js`

**This is a more advanced fix if the above don't work.** The observer is watching for new nodes and might be interfering.

**Add this code around line 169 (in the observer):**

```javascript
observer = new MutationObserver(function(mutations) {
    if (isSwapping) return;
    
    // DON'T react to Dash internal updates
    const isDashUpdate = mutations.some(mutation => {
        return Array.from(mutation.addedNodes).some(node => {
            return node.id && (
                node.id.includes('audio-player') ||
                node.id.includes('waveform-graph') ||
                node.id.includes('segment-metadata')
            );
        });
    });
    
    if (isDashUpdate) {
        console.log('[Dark Mode] Skipping Dash component update');
        return;
    }
    
    // ... rest of observer code
```

---

## 🎯 Recommended Action Plan

### Immediate (5 minutes)
1. ✅ **Add logging to clientside callback** (Fix 1)
2. 🔍 **Check browser console** for errors
3. 🔍 **Check server logs** when audio plays

### If That Doesn't Work (10 minutes)
4. 🔍 **Verify audio element exists** in browser console
5. ✅ **Add diagnostic logging** to server callback (Fix 3)
6. 🔍 **Check if interval is firing** properly

### If Still Broken (20 minutes)
7. 🔧 **Review file browser click handler** - make sure it triggers `load_audio_file`
8. 🔧 **Check callback execution order** - add timing logs
9. 🔧 **Disable dark mode observer temporarily** to test if it's interfering (Fix 4)

---

## 🧪 Testing Protocol

After applying fixes:

### Test 1: Initial Page Load
1. Open dashboard with default audio file
2. **Expected logs in console:**
   ```
   [Playback Sync] Audio element not found (interval: 0)
   [Playback Sync] Audio element not found (interval: 5)
   ```
3. **Expected:** No audio element yet (no file selected)

### Test 2: Click Audio File
1. Click a file in file browser
2. **Expected logs in console:**
   ```
   [Playback Sync] Time: 0.00 s
   ```
3. **Expected logs in server:**
   ```
   [LOAD_AUDIO] Loading audio_id: abc123...
   [AUTO_UPDATE] time=0.0, user_clicked=False, has_segments=True...
   ```

### Test 3: Play Audio
1. Click play button
2. Wait 5 seconds
3. **Expected logs in console:**
   ```
   [Playback Sync] Time: 1.00 s
   [Playback Sync] Time: 6.00 s
   ```
4. **Expected logs in server:**
   ```
   [AUTO_UPDATE] time=1.0, ...
   [AUTO_UPDATE] Active segment: 0.0-5.0
   [AUTO_UPDATE] ✅ Updated waveform cursor to 1.00s and metadata
   ```
5. **Expected visual:**
   - Waveform cursor moves across waveform
   - Segment metadata updates when crossing segment boundaries
   - Persona evaluations update with active segment

### Test 4: Segment Boundary
1. Play audio through a segment transition (e.g., 4.5s → 5.5s)
2. **Expected:**
   - Cursor animates smoothly
   - Metadata updates at 5.0s boundary
   - Old segment info disappears
   - New segment info appears

---

## 📊 Callback Architecture (Current)

```
┌─────────────────────────────────────────────────────────────┐
│ PLAYBACK SYNCHRONIZATION SYSTEM                             │
└─────────────────────────────────────────────────────────────┘

1. USER CLICKS FILE
   └─> file-button click
       └─> selected-audio-store updated
           └─> load_audio_file() callback
               ├─> Fetches segments from backend
               ├─> Extracts waveform data
               ├─> Caches amplitude min/max
               ├─> Creates audio player element  ← CRITICAL
               └─> Outputs to: audio-player-container

2. PLAYBACK SYNC LOOP (Every 1 second)
   └─> playback-sync interval fires
       └─> clientside callback executes
           ├─> Looks for audio-player element
           ├─> Reads currentTime property
           └─> Updates current-time-store

3. UI UPDATE CHAIN
   └─> current-time-store changes
       └─> auto_update_playback() callback
           ├─> Finds active segment
           ├─> Renders waveform with cursor
           ├─> Renders metadata panel
           └─> Outputs to: waveform-graph, segment-metadata

4. WAVEFORM CLICK (Seeking)
   └─> waveform-graph clicked
       └─> clientside callback
           └─> Sets audio.currentTime = clicked_x
```

**Critical Path:** If step 1 doesn't create the audio element properly, steps 2-4 all fail silently.

---

## 💡 Quick Verification Commands

Run these in browser console to diagnose:

```javascript
// 1. Check if audio element exists
console.log('Audio element:', document.getElementById('audio-player'));

// 2. Check if it has currentTime
const audio = document.getElementById('audio-player');
console.log('Current time:', audio ? audio.currentTime : 'NO ELEMENT');

// 3. Manually trigger time update (simulates what callback does)
const audio = document.getElementById('audio-player');
if (audio) {
    console.log('Manually updating store with time:', audio.currentTime);
    // This won't work from console, but shows the logic
}

// 4. Check if interval is running
console.log('Interval component:', document.querySelector('[id="playback-sync"]'));

// 5. Check current stores
// (Can't directly access Dash stores from console)
```

---

## 🎓 Expected Behavior vs Current Behavior

### Expected (Working State)
- ✅ Waveform shows vertical cursor at current playback position
- ✅ Cursor moves smoothly (updates every 1 second)
- ✅ Segment metadata panel updates when crossing segment boundaries
- ✅ Persona evaluations change to show active segment's scores
- ✅ Console logs show periodic time updates
- ✅ Server logs show auto_update_playback firing

### Current (Broken State)
- ❌ Waveform shows NO cursor
- ❌ Cursor doesn't move during playback
- ❌ Segment metadata panel doesn't update
- ❌ Persona evaluations stay on first segment or don't show
- ❓ Console logs: Unknown (need to check)
- ❓ Server logs: Unknown (need to check)

---

## 🔧 Implementation Priority

1. **HIGH PRIORITY - Fix 1:** Add logging to clientside callback (5 min)
   - Immediately shows if audio element is missing
   - Confirms if callback is firing
   
2. **MEDIUM PRIORITY - Diagnostics:** Check console and server logs (2 min)
   - Identifies which part of chain is broken
   
3. **IF NEEDED - Fix 3:** Add server callback logging (2 min)
   - Confirms if time updates are reaching server
   
4. **LAST RESORT - Fix 4:** Dark mode observer isolation (15 min)
   - Only if other fixes don't work

---

## Summary

**Root Cause (Most Likely):** The audio player element isn't being found by the clientside callback, either because:
1. It's not rendered yet when the callback fires
2. It has a different ID or structure after UI changes
3. Dark mode JavaScript is interfering with DOM

**Solution:** Add comprehensive logging to pinpoint exact failure point, then fix accordingly.

**Estimated Fix Time:** 10-30 minutes depending on root cause
