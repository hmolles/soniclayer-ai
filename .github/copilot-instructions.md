# Copilot Instructions for SonicLayer AI

This file gives concise, actionable guidance for AI coding agents working in this repository. Keep edits tight and specific to the codebase patterns.

- Big picture: FastAPI backend (entry: `app/main.py`) provides endpoints for uploading audio, retrieving segments and serving audio. Processing pipeline:
  - `app/routes/evaluate.py` receives uploads, orchestrates transcription (`app/services/transcryption.py`), classification (`app/services/classifier.py`), and persona feedback via the Langflow client (`app/services/langflow_client.py`).
  - Intermediate data is persisted in Redis using keys like `transcript_segments:{audio_id}`, `classifier_output:{audio_id}`, and `persona_feedback:{agent}:{audio_id}:{segment_id}`. See `app/routes/segments.py` for reassembly logic.
  - Workers (in `app/workers/`) run persona or agent-specific tasks and push results into Redis.
  - PersonaAgent base class (`app/models/personas/persona_agent.py`) provides evaluation framework; **GenZAgent and AdvertiserAgent are fully implemented**. Additional persona workers exist (parents, regional) but don't yet use PersonaAgent base class.
  - **Langflow deployment:** Run via Docker container for LLM-based persona evaluations. Set `LANGFLOW_BASE_URL` env var (default: http://localhost:7860).

- Quick dev tasks and commands (from README):
  - Install deps: `pip install -r requirements.txt`
  - Start Redis & Langflow (required): `docker-compose up -d`
  - Verify Redis: `redis-cli ping`
  - Run backend: `uvicorn app.main:app --reload`
  - Run dashboard: `python dashboard/app.py`
  - Start RQ workers: `rq worker transcript_tasks`
  - Run tests: `pytest tests/`

- Patterns and conventions to follow when editing:
  - Redis-centric dataflow: prefer writing/reading JSON-serializable dicts to Redis with explicit key patterns (see `app/routes/evaluate.py` and `app/routes/segments.py`). Use TTL (ex: `ex=86400`) for cached derived data.
  - Service layer: synchronous helper functions live in `app/services/` and are invoked by routes and workers. Add new logic there and keep routers thin.
  - Langflow integrations: calls to Langflow are made via `app/services/langflow_client.py` — treat this as an external RPC; handle network failures gracefully and store error objects in Redis under the same persona keys rather than throwing.
  - Audio files: served from `uploads/` with file names `{audio_id}.wav`. Routes assume local FS access.
  - Classification: zero-shot HuggingFace pipelines are used (`app/services/classifier.py`) — expect model loading cost; prefer module-level singletons and avoid re-loading models per-request.

- Tests & CI notes:
  - Tests live under `tests/` and use pytest. They assume Redis and local model availability for integration tests — if Redis is not available, mock `app.services.cache.redis_conn` or run a local Redis instance for test runs.
  - Keep unit tests deterministic: mock external model/pipeline calls and Langflow RPCs where possible.

- Common edits you'll be asked to make (examples):
  - Add a new segment-level classifier: implement function in `app/services/classifier.py`, call it from `app/routes/evaluate.py`, and persist under `classifier_output:{audio_id}`.
  - Change persona weights: update `app/services/coordinator.py`'s `weights` map and ensure downstream consumers still read the same keys.

- Files to inspect for similar examples:
  - `app/routes/evaluate.py` — orchestration and Redis key patterns
  - `app/routes/segments.py` — enrichment and caching
  - `app/services/transcryption.py` — Whisper transcription helper
  - `app/services/classifier.py` — HF classification pipeline
  - `app/services/langflow_client.py` — external agent RPC
  - `app/workers/` — examples of background task patterns (advertiser_worker.py, genz_worker.py, parents_worker.py, regional_worker.py)
  - `app/models/personas/persona_agent.py` — base class for persona evaluation logic

- Error handling and logging:
  - Routes catch and log Langflow/external failures and store them as objects in Redis rather than failing the whole request. Follow that pattern for any new external calls.
  - Use Python's `logging` module; avoid printing.

- What not to change without discussion:
  - Redis key naming conventions and TTLs — many components rely on these exact keys.
  - The FastAPI route signatures (URLs) used by the dashboard: `/evaluate/`, `/segments/{audio_id}`, `/audio/{audio_id}`.

If any behaviors or external dependencies are unclear (Langflow chain names, Redis db choices, exact worker queue names), ask the maintainers. Want me to revise any section or add examples from other files?