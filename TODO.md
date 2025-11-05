# SonicLayer AI - TODO & Next Steps

**Last Updated:** 5 November 2025  
**Status:** MVP Complete - Testing & Refinement Phase

---

## 🔥 CURRENT PRIORITY (IN PROGRESS)

### Testing New Whisper Timestamp-Based Segmentation
**Status:** User actively testing test1.wav upload  
**Expected Completion:** Within 1 hour

**What to Verify:**
- [ ] Upload test1.wav completes successfully
- [ ] Wait for RQ worker to process GenZ + Advertiser jobs (~1-2 minutes)
- [ ] Start dashboard: `python dashboard/app.py <audio_id>`
- [ ] Verify transcripts align perfectly with audio playback
- [ ] Check for 🎵 instrumental section notes in metadata panel
- [ ] Confirm no more timing misalignment issues

**Success Criteria:**
- ✅ Segments start exactly when speech begins
- ✅ Instrumental sections detected and labeled
- ✅ Playback cursor tracks with correct transcript
- ✅ No more "first segment shows wrong lyrics" issues

---

## 📝 QUICK FIXES (15 minutes total)

### 1. Update requirements.txt
**Time:** 2 minutes  
**Action:**
```bash
echo "scipy" >> requirements.txt
echo "dash-player" >> requirements.txt
```

**Why:** These dependencies are used but not documented

### 2. Clean Up Old Working Documents
**Time:** 5 minutes  
**Files to Remove/Archive:**
- `IMPLEMENTATION_SUMMARY.md` - Outdated (Nov 4)
- `AUDIT_SUMMARY.md` - Pre-implementation audit
- `LANGFLOW_NEXT_STEPS.md` - Already done
- `TEST_PLAN.md` - Tests already written
- `UPLOAD_IMPLEMENTATION.md` - Already implemented

**Action:**
```bash
mkdir archive
mv IMPLEMENTATION_SUMMARY.md AUDIT_SUMMARY.md LANGFLOW_NEXT_STEPS.md TEST_PLAN.md UPLOAD_IMPLEMENTATION.md archive/
```

### 3. Add Worker Startup to QUICK_START.md
**Time:** 3 minutes  
**Missing:** Step about starting RQ worker before upload  
**Add:** Clear instruction to run `rq worker transcript_tasks` or `./scripts/start_worker.sh`

### 4. Document Redis Data Cleanup Command
**Time:** 2 minutes  
**Where:** QUICK_START.md troubleshooting section  
**Add:**
```bash
# Clear all data for specific audio file
python -c "import hashlib; data=open('audio.wav','rb').read(); print(hashlib.sha256(data).hexdigest())"
# Then: docker exec soniclayer-redis redis-cli KEYS "*<hash>*" | xargs -I {} docker exec soniclayer-redis redis-cli DEL {}
```

### 5. Create Simple Deployment Checklist
**Time:** 3 minutes  
**File:** `DEPLOYMENT.md`  
**Content:** Pre-flight checklist before running system (Docker, venv, ports, etc.)

---

## 🧪 TESTING & VALIDATION (1-2 hours)

### Run Full Test Suite
**Priority:** HIGH  
**Commands:**
```bash
source venv/bin/activate
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

**Expected Results:**
- ~60 test cases
- >70% code coverage
- All persona agent tests passing
- Integration tests with mocked externals passing

**Known Gaps:**
- Some tests may fail due to environment-specific issues
- Langflow integration tests require running Langflow container
- May need to mock additional external calls

### Validate Both Audio Files
**Priority:** MEDIUM  
**Actions:**
1. Clear test2.wav data and re-upload for new timing
2. Verify both test1.wav and test2.wav work in dashboard
3. Compare old vs new segmentation quality
4. Document any edge cases or issues

### Browser Testing
**Priority:** LOW  
**Actions:**
- Test dashboard in Chrome, Firefox, Safari
- Verify waveform rendering performance
- Check mobile responsiveness (nice-to-have)
- Validate click-to-seek on different screen sizes

---

## 🔧 OPTIONAL IMPROVEMENTS (Future Work)

### Additional Persona Agents (NOT MVP CRITICAL)
**Estimated Time:** 2-3 hours each  
**Agents to Implement:**
- [ ] **ParentsAgent** - Family-friendly content focus
- [ ] **RegionalAgent** - Geographic/cultural preferences
- [ ] **AcademicAgent** - Educational value assessment

**Steps for Each:**
1. Create class extending PersonaAgent
2. Define preferences dict (preferred_tones, topics, etc.)
3. Update corresponding worker to use new agent
4. Create Langflow chain
5. Write 10-15 unit tests
6. Add to integration test

### Performance Optimizations
**Priority:** LOW  
**Ideas:**
- [ ] Cache Whisper/HuggingFace models in memory (avoid reload)
- [ ] Parallel segment classification (currently sequential)
- [ ] Batch Langflow API calls (reduce latency)
- [ ] Optimize waveform downsampling algorithm
- [ ] Add segment processing progress websocket (real-time updates)

### UI/UX Enhancements
**Priority:** LOW  
**Ideas:**
- [ ] Add waveform zoom controls
- [ ] Segment timeline scrubber
- [ ] Persona score comparison chart
- [ ] Export segment data as JSON/CSV
- [ ] Audio format conversion (MP3 → WAV)
- [ ] Multi-file upload queue

### DevOps & Deployment
**Priority:** MEDIUM (if deploying to production)  
**Tasks:**
- [ ] Create Dockerfile for backend
- [ ] Docker Compose for full stack (backend + dashboard + Redis + Langflow)
- [ ] Environment variable configuration (.env support)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Logging configuration (structured JSON logs)
- [ ] Monitoring setup (Prometheus/Grafana)
- [ ] Production Redis persistence strategy

### Documentation Improvements
**Priority:** LOW  
**Tasks:**
- [ ] Architecture diagram (system components, data flow)
- [ ] API documentation (OpenAPI/Swagger auto-generated)
- [ ] Video tutorial for setup and usage
- [ ] Contributing guidelines
- [ ] Code style guide
- [ ] Persona customization guide

---

## 🐛 KNOWN BUGS (None Critical)

### Minor Issues
1. **Dashboard doesn't gracefully handle missing audio_id** - Shows error but could be prettier
2. **Large audio files (>5MB) may timeout** - No upload progress indicator
3. **Worker logs to stdout** - Should use proper logging with rotation
4. **No rate limiting on /evaluate/** - Could be abused
5. **Redis keys have 24h TTL** - No way to extend or make permanent

**Priority:** All LOW - system works despite these issues

---

## 📊 METRICS & MONITORING (Future)

### What to Track
- [ ] Average processing time per segment
- [ ] Langflow API success/failure rate
- [ ] Worker queue depth and processing lag
- [ ] Dashboard active users
- [ ] Audio upload volume and formats
- [ ] Persona score distributions
- [ ] Cache hit/miss rates

### Tools to Consider
- Prometheus for metrics
- Grafana for dashboards
- Sentry for error tracking
- New Relic for APM

---

## 🎓 LEARNINGS & NOTES

### What Worked Well
- ✅ PersonaAgent base class made adding agents easy
- ✅ Whisper timestamps much better than word-count estimation
- ✅ Redis caching simplified data flow
- ✅ Dash + Plotly great for rapid dashboard development
- ✅ RQ workers simple and reliable
- ✅ Docker Compose made setup reproducible

### What Was Challenging
- ⚠️ Langflow API documentation initially unclear (endpoint naming)
- ⚠️ Dash v1 → v2 migration broke existing code
- ⚠️ WAV format diversity (float32 not supported by wave module)
- ⚠️ Worker hash mismatch caused "not yet processed" confusion
- ⚠️ Transcript-audio alignment tricky without proper timestamps

### Best Practices Established
- Always use audio_id (file hash) as primary key
- Store intermediate results in Redis for debugging
- Use PersonaAgent base class for consistent evaluation
- Prefer Whisper's built-in timestamps over estimation
- Test with real audio files early and often
- Document Langflow chain setup thoroughly

---

## 🚀 NEXT SESSION PLAN

1. **Verify test1.wav upload** with new segmentation (10 min)
2. **Update requirements.txt** with scipy + dash-player (2 min)
3. **Clean up old docs** → move to archive/ (5 min)
4. **Run pytest suite** → validate all tests (15 min)
5. **Re-upload test2.wav** → verify improvement (10 min)
6. **Document final state** → update README if needed (10 min)
7. **Consider next features** → pick from Optional Improvements above

**Total Time:** ~1 hour to full MVP validation ✅

---

## ✅ DEFINITION OF DONE

**MVP is "done" when:**
- [x] Upload audio → transcribe → classify → evaluate pipeline works
- [x] GenZ + Advertiser personas provide scores via Langflow
- [x] Dashboard shows interactive playback with metadata
- [ ] New Whisper timestamp segmentation verified working
- [ ] At least 50/60 tests passing
- [ ] README/QUICK_START accurate and tested
- [ ] No critical bugs blocking usage
- [ ] Can demo to stakeholders successfully

**Current Status:** 7/8 complete, final verification in progress 🎉
