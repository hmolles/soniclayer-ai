# SonicLayer AI - Replit Project

## Overview
SonicLayer AI is an intelligent audio analysis system that transcribes, classifies, and simulates audience reactions to broadcast content using machine learning. It was imported from GitHub to Replit.

## Project Status
**Current State:** ✅ Fully operational in Replit with pre-processed data

The application is running with pre-processed audio segments. New audio processing requires large ML dependencies (PyTorch, Whisper, Transformers) that exceed Replit's disk quota and should be done locally, then uploaded to Replit for visualization and analysis.

## Architecture

### Backend (FastAPI)
- **Location:** `app/main.py`
- **Port:** 8000 (localhost)
- **Routes:**
  - `/evaluate/` - Audio upload endpoint
  - `/re-evaluate/{audio_id}` - Re-run evaluations with updated persona settings
  - `/segments/{audio_id}` - Get segment data
  - `/audio/{audio_id}` - Serve audio files
  - `/status/{audio_id}` - Processing status

### Frontend (Dash Dashboard)
- **Location:** `dashboard/app.py`
- **Port:** 5000 (configured for Replit webview)
- **Architecture:** Single-page application with sidebar file browser
- **Features:** 
  - Real-time waveform cursor tracking during playback
  - Auto-updating metadata panel showing current segment
  - File browser sidebar for selecting audio files
  - Admin modal for creating new personas
  - Clickable waveform for jumping to specific timestamps

### Services
- **Redis:** Caching and job queue (port 6379)
- **RQ Workers:** Background job processing
- **Langflow:** LLM chain orchestration (optional, port 7860)

## Dependencies

### Core (Installed)
- FastAPI, Uvicorn
- Redis, RQ
- Dash, Plotly, Dash-player
- NumPy, Requests

### ML (Not Installed - Too Large)
- PyTorch (~900MB)
- Transformers
- OpenAI Whisper
- Librosa, SciPy

## Running Locally
To run the full application on your local machine:

1. Clone the repository
2. Install all dependencies: `pip install -r requirements.txt`
3. Start Redis: `redis-server`
4. Start backend: `uvicorn app.main:app --reload`
5. Start worker: `rq worker transcript_tasks`
6. Upload audio and launch dashboard

See `README.md` and `QUICK_START.md` for detailed instructions.

## Recent Changes (November 2025)
- **✅ Modern Clean UI Design** - Complete redesign inspired by contemporary apps (November 5, 2025)
  - **Clean, minimal aesthetic** with light color scheme and soft shadows
  - **Very rounded corners** (16-24px) on all cards and elements
  - **Soft, subtle shadows** with multiple elevation levels
  - **Card-based layout** with elevated white surfaces
  - **Light gray background** (#F5F5F5) for better contrast
  - **Blue accent color** (#2196F3) for primary actions
  - **Improved spacing** and typography using Inter font
  - **Smooth transitions** (0.2-0.3s) on all interactive elements
  - **Responsive design** with mobile-friendly breakpoints
  - **Clean scrollbars** with custom styling
  - **Minimal borders** and cleaner visual hierarchy
  
- **✅ Three-Tier Hybrid Summary System** - Multi-level summary aggregation (November 5, 2025)
  - **Tier 1: File Browser Badges** - Color-coded persona score badges on each audio file
  - **Tier 2: Collapsible Summary Panel** - Quick overview on Analysis tab (above waveform)
    - Toggle to show/hide aggregated persona scores
    - Color-coded ratings (Green 4.0+, Blue 3.0-3.9, Orange 2.0-2.9, Red <2.0)
    - One-click access to detailed statistics
  - **Tier 3: Summary Tab** - Comprehensive analytics with visualizations
    - Score distribution charts for each persona
    - Top & worst performing segments
    - Confidence metrics
  - **Performance Optimization:**
    - Backend `/summary/{audio_id}` endpoint with Redis caching (24-hour TTL)
    - 5x speedup: uncached 18ms → cached 3.6ms
    - Fetched once per audio scan (eliminates redundant HTTP calls)
    - Component architecture via `dashboard/components/summary_panel.py`
- **✅ Clickable Sidebar File Browser** - Single-page design with intuitive file selection
  - Beautiful card-based file browser in left sidebar
  - Click any audio file to instantly load its analysis
  - Visual highlighting shows currently selected file
  - "3 files available" counter
- **✅ Real-time Auto-updating** - VERIFIED WORKING (Core Feature)
  - Waveform cursor moves in real-time during audio playback
  - Segment highlighting updates automatically as playback progresses
  - Metadata panel updates to show current segment transcript and evaluations
  - Clickable waveform for instant seeking
- **✅ Persona Editing with Re-evaluation** - Complete admin workflow
  - Inline expansion UI for editing persona details (name, emoji, description, prompts)
  - Real-time JSON validation with error highlighting
  - Save with toast notifications
  - Re-evaluate button to re-run analysis with updated persona settings
  - Automatic dashboard refresh after re-evaluation
- **Dynamic Persona Registry System** - Unlimited personas via central config
- **Admin Interface** - Web-based UI for adding/editing personas without code changes
- **JSON Validation** - Real-time validation for persona prompts
- **Azure OpenAI Integration** - Replaced Langflow with direct Azure GPT-4o-mini calls

## User Preferences
- Prefers scalable architecture that doesn't require code changes for new features
- Values admin interfaces for non-technical users

## Known Limitations in Replit
- **New audio processing** - Requires ML dependencies too large for Replit (transcription with Whisper must be done locally, then upload results to Replit for visualization)
- **Persona evaluations** - Fully functional using Azure OpenAI API calls (no local ML dependencies needed)

## Running in Replit
The application is currently running with 4 workflows:
1. **backend** - FastAPI server on port 8000
2. **dashboard** - Dash visualization on port 5000 (webview)
3. **redis** - Redis server on port 6000
4. **worker** - RQ worker for processing persona evaluations via Azure OpenAI

Simply open the webview to see the dashboard with pre-processed audio analysis.

### Re-evaluation Feature
The re-evaluation feature is fully functional in Replit:
1. Edit any persona in the Admin panel
2. Click "Save Changes"
3. Click "🔄 Re-evaluate Audio" in the success toast
4. Wait ~15-60 seconds for Azure OpenAI to process all segments
5. Dashboard auto-refreshes with updated evaluations

## Deployment
For production deployment guidance, see `DEPLOYMENT.md` which covers:
- Docker Compose setup
- Systemd service configuration
- Environment variables
- Security considerations
