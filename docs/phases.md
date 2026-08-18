# Integration Phases
## Remaining Work: Verified Modules → Shipped Pipeline

> Modules already built & verified: **VAD (Silero)**, **SBD (OpenCV HSV Histogram)**, **Spatial Math OCR (Pix2Text)**. These phases cover everything remaining.

---

### Phase 1: Core Module Stitching — ✅ Complete, in active debugging
**Goal:** Get the three verified modules talking to each other as a single offline pipeline, no APIs yet.
- ✅ `orchestrator.py` runs VAD → SBD → correlation → OCR in sequence.
- ✅ `correlator.py` matches silence windows to nearby scene-change timestamps.
- ✅ `vad_engine.py` — Silero VAD, `detect_silences(audio_path, min_duration)`.
- ✅ `scene_detector.py` — 64-bin (8×8) HSV histogram differencing, Hue+Saturation only, `detect_scene_changes(video_path)`.
- ✅ `ocr_engine.py` — Pix2Text with bounded 900×450 ROI cropping (widened from 500×500 after real footage showed equations getting clipped), `extract_latex_at_timestamp(video_path, timestamp)`.
- ✅ Disk-based intermediate storage: extracted audio via `audio_extractor.py`, TTS clips under `data/intermediate/{job_id}/`, plus a `debug.json` per job logging OCR LaTeX + LLM output per segment for troubleshooting.
- ✅ Validated on real NPTEL footage — found and fixed a `torch.hub` EOFError, a Pix2Text image-type mismatch, an `.env` loading bug, and OCR crop clipping causing malformed multi-equation LaTeX.
- **Exit criteria:** Given a raw video, the pipeline outputs a structured list of `{timestamp, latex_string}` entries with zero manual intervention. **Running end-to-end; OCR/LLM output quality is still being tuned against real footage.**

### Phase 2: API Integration (LLM + TTS)
**Goal:** Convert extracted LaTeX into playable audio clips.
- ✅ Build `llm_client.py`: async wrapper for Groq API (primary) with Gemini API as a configurable fallback. **Done — Groq `llama-3.1-8b-instant` primary, Gemini `gemini-2.0-flash` fallback on 429/timeout, batch-safe processing.**
- 🔲 Build `tts_client.py`: async Edge-TTS wrapper, generating `.mp3`/`.wav` per description, saved to `data/intermediate/`. **Done — includes `synthesize_fitted()` for duration checking.**
- 🔲 Add duration-checking logic: compare generated audio length to the available silence window; if too long, request a shorter LLM description (dynamic prompt adjustment) rather than truncating audio mid-sentence. **Done — `synthesize_fitted()` shortens the text and re-synthesizes until it fits, or logs a warning if it can't.**
- ✅ Add retry/backoff and per-segment error isolation per `rules.md`. **Done in `llm_client.py`; orchestrator skips failed segments individually.**
- **Exit criteria:** Given the Phase 1 output JSON, the system produces a folder of correctly-named, correctly-timed TTS audio clips.

### Phase 3: Backend & Frontend Setup — ✅ Complete
**Goal:** Wrap the pipeline in a usable async service with a dashboard.
- ✅ `app.py` (Streamlit): dark→light theme, two-column layout, upload/progress/download UI, How it Works section.
- ✅ `main.py` (FastAPI) with `/upload`, `/status/{job_id}`, `/download/{job_id}` endpoints (`api/routes.py`, `api/schemas.py`).
- ✅ Async job orchestration via `asyncio.create_task`, in-memory `jobs` dict for status tracking.
- ✅ `app.py` calls the real endpoints via `requests` — no more mock.
- **Exit criteria:** A user can upload a video via the browser, watch progress update, and download a processed video — all through the UI, no manual script running. **Met — confirmed working end-to-end against real footage.**

### Phase 4: FFmpeg Video Reassembly
**Goal:** Produce the final accessible video artifact.
- ✅ Build `muxer.py`: insert each TTS clip into the original audio track at its matched silence window using FFmpeg filters (`adelay`, `amix`, or segment-based concat depending on approach). **Done — `amix` with `adelay`-shifted clips; falls back to a pure stream copy if no clips were generated.**
- 🔲 Handle edge cases: TTS clip longer than silence window (already mitigated in Phase 2, but add a hard trim fallback), overlapping windows, and videos with zero detected math segments (pass-through, no-op). **Zero-segment pass-through done; overlapping windows and hard-trim fallback still open.**
- ✅ Re-mux final audio track with original video stream (copy video codec, no re-encoding, to preserve speed and quality). **Done — `-c:v copy` in `muxer.py`.**
- 🔲 Run full end-to-end tests on complete NPTEL lecture videos (30–60+ min) to confirm timing accuracy and stability under the 6GB RAM ceiling.
- **Exit criteria:** Final output video plays with correctly-timed, audible math descriptions inserted into silence, with no drift, overlap, or corruption — verified on full-length real lectures.
