# SonicLayer AI

> **Status (Nov 5, 2025):** 🎉 **MVP COMPLETE** - Full pipeline operational. Currently testing new Whisper timestamp-based segmentation for perfect audio-transcript alignment. See [TODO.md](TODO.md) for next steps.

SonicLayer AI is an intelligent audio insight system for producers and content teams. It transcribes, classifies, and simulates audience reactions to broadcast content in real time.

## Features
- WAV audio upload and transcription via **Whisper with accurate timestamps**
- Segment classification (topic, tone) using HuggingFace
- **Langflow-powered persona evaluation** (Gen Z, Advertiser) via LLM chains
- **Interactive dashboard** with waveform overlays and playback sync
- **Click-to-seek** and real-time metadata panel with color-coded persona scores
- **Instrumental section detection** (🎵 notes for music-only segments)
- Redis-based caching and RQ background job processing

## Tech Stack
- Python 3.10+
- FastAPI (async web framework)
- Redis + RQ (job queue and caching)
- Whisper (local transcription)
- HuggingFace Transformers (classification)
- **Langflow** (LLM chain orchestration)
- **LM Studio** (local LLM inference)
- Dash + Plotly (interactive dashboard)

## Setup
1. Clone the repo
2. Install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Start Redis and Langflow (Docker with persistence):
   ```bash
   docker compose up -d
   ```
   Verify Redis:
   ```bash
   redis-cli ping  # Should return "PONG"
   ```
   
4. **Configure Langflow chains** (one-time setup):
   - Access Langflow at http://localhost:7860
   - Follow the detailed guide: [docs/LANGFLOW_SETUP_GUIDE.md](docs/LANGFLOW_SETUP_GUIDE.md)
   - Create `genz_chain` and `advertiser_chain` flows
   - Connect to LM Studio (localhost:1234) for LLM inference
   - Quick reference: [docs/LANGFLOW_QUICK_REFERENCE.md](docs/LANGFLOW_QUICK_REFERENCE.md)

5. Run FastAPI backend:
   ```bash
   uvicorn app.main:app --reload
   ```
   
6. Run Dash dashboard (after uploading audio):
   ```bash
   # Use the audio_id returned from /evaluate/
   python dashboard/app.py <audio_id>
   
   # Example:
   python dashboard/app.py ebeb643592f3ae3097bba2e0334414df2d8652f8f73f6ab74d1a61c79b544275
   ```
   Then open http://localhost:8050 in your browser.
   
7. Start RQ workers:
   - **macOS users** (avoids fork crash):
     ```bash
     ./scripts/start_worker.sh
     ```
   - **Linux/Windows users**:
     ```bash
          rq worker transcript_tasks
     ```

## API Endpoints
- `POST /evaluate/` – Upload WAV file, triggers transcription, classification, and persona evaluation
- `GET /segments/{audio_id}` – Get enriched segment data with persona scores
- `GET /status/{audio_id}` – Get processing status
- `GET /audio/{audio_id}` – Serve audio file

## Integration Testing
Run end-to-end test with Langflow integration:
```bash
python scripts/integration_test.py test1.wav
```
This will:
1. Upload audio to `/evaluate/`
2. Wait for Langflow persona processing (1-2 minutes)
3. Display GenZ and Advertiser scores for each segment
4. Save results to `test_results_{audio_id}.json`

## Tests
Run all tests with:
```bash
pytest tests/
```

## Documentation
- **[docs/LANGFLOW_SETUP_GUIDE.md](docs/LANGFLOW_SETUP_GUIDE.md)** - Complete Langflow chain setup (15-20 min)
- **[docs/LANGFLOW_QUICK_REFERENCE.md](docs/LANGFLOW_QUICK_REFERENCE.md)** - One-page cheat sheet
- **[DOCS_INDEX.md](DOCS_INDEX.md)** - Full documentation index
     ```

## API Endpoints
- `POST /evaluate/` – Upload WAV file
- `GET /segments/{audio_id}` – Get enriched segment data
- `GET /status/{audio_id}` – Get processing status
- `GET /audio/{audio_id}` – Serve audio file

## Tests
Run all tests with:
```bash
pytest tests/