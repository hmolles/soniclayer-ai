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
- **New audio processing** - Requires ML dependencies too large for Replit (process locally, upload results)
- **Redis/RQ workers** - Not running (not needed for viewing pre-processed data)
- **Langflow** - Not available (replaced with Azure OpenAI direct calls)

## Running in Replit
The application is currently running with 4 workflows:
1. **backend** - FastAPI server on port 8000
2. **dashboard** - Dash visualization on port 5000 (webview)
3. **redis** - Redis server on port 6000
4. **worker** - RQ worker (not running - not needed for viewing)

Simply open the webview to see the dashboard with pre-processed audio analysis.

## Deployment
For production deployment guidance, see `DEPLOYMENT.md` which covers:
- Docker Compose setup
- Systemd service configuration
- Environment variables
- Security considerations
