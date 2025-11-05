# 🚀 SonicLayer AI - Quick Start Guide

**Get up and running in 5 minutes!**

---

## Prerequisites

- Python 3.10+
- Docker Desktop (for Redis & Langflow)
- LM Studio with a loaded model (for LLM inference)

---

## Step 1: Start Services (One-time setup)

```bash
# Start Redis and Langflow containers
docker compose up -d

# Verify Redis is running
redis-cli ping  # Should return "PONG"

# Verify Langflow is accessible
curl http://localhost:7860/health
```

---

## Step 2: Configure Langflow Chains (One-time setup)

1. Open Langflow UI: http://localhost:7860
2. Create two flows following [docs/LANGFLOW_SETUP_GUIDE.md](docs/LANGFLOW_SETUP_GUIDE.md):
   - `genz_chain` - Gen Z persona evaluation
   - `advertiser_chain` - Brand safety evaluation
3. Connect both to LM Studio (http://host.docker.internal:1234/v1)

**Quick test:**
```bash
curl -X POST http://localhost:7860/api/v1/run/genz_chain \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-pYbkputG1PLU6968zp5NK44ZaZvvA9iuqbOoVhuAYAs" \
  -d '{"input_value": "{\"text\": \"This is awesome!\", \"topic\": \"Entertainment\", \"tone\": \"Excited\"}", "output_type": "chat", "input_type": "chat"}'
```

---

## Step 3: Start the Backend

**Terminal 1:**
```bash
cd /Users/hani/Documents/SonicAI
source venv/bin/activate
uvicorn app.main:app --reload
```

Backend will be available at: http://localhost:8000

---

## Step 4: Start the Worker

**Terminal 2:**
```bash
cd /Users/hani/Documents/SonicAI
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  # macOS only
source venv/bin/activate
rq worker transcript_tasks
```

Or use the helper script:
```bash
./scripts/start_worker.sh
```

---

## Step 5: Upload Audio

**Terminal 3:**
```bash
cd /Users/hani/Documents/SonicAI
source venv/bin/activate

# Upload your audio file
curl -X POST http://localhost:8000/evaluate/ \
  -F "file=@test1.wav" \
  | python -m json.tool

# Save the audio_id from the response!
```

**Example response:**
```json
{
  "audio_id": "ebeb643592f3ae3097bba2e0334414df2d8652f8f73f6ab74d1a61c79b544275",
  "status": "processing",
  "segment_count": 14,
  "job_ids": {
    "genz": "abc-123",
    "advertiser": "def-456"
  }
}
```

---

## Step 6: Wait for Processing

Processing takes ~5-10 seconds per segment (LLM calls are slow).

**Check progress:**
```bash
# Replace with your audio_id
AUDIO_ID="ebeb643592f3ae3097bba2e0334414df2d8652f8f73f6ab74d1a61c79b544275"

curl -s http://localhost:8000/segments/$AUDIO_ID | \
  python -c "import sys, json; data=json.load(sys.stdin); segs=data['segments']; \
  print(f'GenZ: {sum(1 for s in segs if \"genz\" in s)}/{len(segs)}'); \
  print(f'Advertiser: {sum(1 for s in segs if \"advertiser\" in s)}/{len(segs)}')"
```

Or use the integration test script:
```bash
python scripts/integration_test.py test1.wav
```

---

## Step 7: View Results in Dashboard

**Terminal 4:**
```bash
cd /Users/hani/Documents/SonicAI
source venv/bin/activate

# Replace with your audio_id
python dashboard/app.py ebeb643592f3ae3097bba2e0334414df2d8652f8f73f6ab74d1a61c79b544275
```

Then open in browser: **http://localhost:8050**

---

## Dashboard Features

- 🎵 **Waveform visualization** with segment highlights
- 🎧 **Audio playback** with sync to waveform
- 🔥 **Gen Z scores** - Score (1-5), opinion, rationale, confidence
- 💼 **Advertiser scores** - Brand safety analysis
- 📊 **Color-coded badges** - Red (1-2), Amber (3), Green (4-5)
- 📝 **Full transcripts** with topic/tone classification

---

## Troubleshooting

### "Worker crashes with fork error" (macOS)
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

### "Segments show 'not yet processed'"
- Wait longer (check processing progress with curl command above)
- Verify worker is running: `ps aux | grep "rq worker"`
- Check worker logs in Terminal 2

### "Langflow connection failed"
- Verify LM Studio is running on localhost:1234
- Check Langflow health: `curl http://localhost:7860/health`
- Verify chains are created: Check Langflow UI

### "Redis connection refused"
```bash
docker ps | grep redis  # Should show running container
docker compose up -d    # Restart if needed
```

---

## Common Commands

```bash
# Clear all Redis data (fresh start)
docker exec soniclayer-redis redis-cli FLUSHDB

# Check RQ job queue status
docker exec soniclayer-redis redis-cli LLEN "rq:queue:transcript_tasks"

# View persona feedback for an audio
docker exec soniclayer-redis redis-cli KEYS "persona_feedback:*:YOUR_AUDIO_ID:*"

# Check backend logs
# (visible in Terminal 1 where uvicorn is running)

# Check worker logs
# (visible in Terminal 2 where rq worker is running)
```

---

## Expected Processing Times

- **Upload + Transcription**: ~10-30 seconds (depends on audio length)
- **Classification**: ~1 second per segment
- **Persona evaluation**: ~5-10 seconds per segment per persona
- **Total for 14 segments**: ~2-4 minutes

---

## What's Next?

1. **Add more personas** - Follow [docs/LANGFLOW_SETUP_GUIDE.md](docs/LANGFLOW_SETUP_GUIDE.md)
2. **Customize prompts** - Edit chains in Langflow UI
3. **Run tests** - `pytest tests/`
4. **Explore API** - http://localhost:8000/docs (FastAPI Swagger UI)

---

## Need Help?

- **Full setup guide**: [docs/LANGFLOW_SETUP_GUIDE.md](docs/LANGFLOW_SETUP_GUIDE.md)
- **Quick reference**: [docs/LANGFLOW_QUICK_REFERENCE.md](docs/LANGFLOW_QUICK_REFERENCE.md)
- **All documentation**: [DOCS_INDEX.md](DOCS_INDEX.md)

**Enjoy analyzing your audio! 🎉**
