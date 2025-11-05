# SonicLayer AI - Replit Project

## Overview
SonicLayer AI is an intelligent audio analysis system that transcribes, classifies, and simulates audience reactions to broadcast content using machine learning. It was imported from GitHub to Replit.

## Project Status
**Current State:** Partially configured for Replit environment

The full application requires large ML dependencies (PyTorch, Whisper, Transformers) that exceed Replit's disk quota. A simplified version is running to demonstrate the project structure.

## Architecture

### Backend (FastAPI)
- **Location:** `app/main.py`
- **Port:** 8000 (localhost)
- **Routes:**
  - `/evaluate/` - Audio upload endpoint
  - `/segments/{audio_id}` - Get segment data
  - `/audio/{audio_id}` - Serve audio files
  - `/status/{audio_id}` - Processing status

### Frontend (Dash Dashboard)
- **Location:** `dashboard/app.py`
- **Port:** 5000 (configured for Replit webview)
- **Features:** Waveform visualization, audio playback, persona scores

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

## Recent Changes
- Configured for Replit environment
- Created simplified startup script (`start_app.py`)
- Installed core dependencies (excluding ML packages)
- Set up Redis via Nix
- Created uploads/ and logs/ directories

## User Preferences
None recorded yet.

## Known Issues
- ML dependencies too large for Replit's disk quota
- Full pipeline requires local setup or larger cloud instance
- Langflow and LM Studio not available in Replit
- Redis and RQ workers not running in Replit environment
- Background job processing disabled

## Running the Simplified Demo
The simplified FastAPI app can be tested locally without ML dependencies:
```bash
python start_app.py
# Visit http://localhost:5000 to see the setup information page
```

## Deployment
For production deployment guidance, see `DEPLOYMENT.md` which covers:
- Docker Compose setup
- Systemd service configuration
- Environment variables
- Security considerations
