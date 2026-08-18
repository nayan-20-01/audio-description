# 🔴 UPDATE IT REGULARLY 🔴
## Development Session Memory — NPTEL Audio Description Pipeline

> This file is the single source of truth for session continuity. Update it at the end of every working session, and re-read it at the start of every new session (human or AI-assisted).

---

## What Has Been Completed
- ✅ **`vad_engine.py`** — Silero VAD via `torch.hub`, lazy singleton model load, `detect_silences(audio_path, min_duration)` returns gap windows between speech segments.
- ✅ **`scene_detector.py`** — 8×8 (64-bin) HSV histogram differencing, Hue+Saturation channels only (Value ignored), `detect_scene_changes(video_path)`, with a `min_gap_seconds` debounce to avoid duplicate detections on the same board change.
- ✅ **`ocr_engine.py`** — Pix2Text (`recognize_formula`), lazy singleton model load, bounded 900×450 ROI crop (widened from an initial 500×500 square after real-footage testing showed clipping) with explicit empty-crop guarding, `extract_latex_at_timestamp(video_path, timestamp)`.
- ✅ **`llm_client.py`** — Groq primary / Gemini fallback, batch-safe. Lives at `src/pipeline/llm_client.py`.
- ✅ **`tts_client.py`** — Edge-TTS wrapper with `synthesize_fitted()` for duration-window fitting.
- ✅ **`audio_extractor.py`** — FFmpeg video→wav.
- ✅ **`correlator.py`** — matches silence windows to nearby scene changes.
- ✅ **`muxer.py`** — FFmpeg `adelay`+`amix` insertion, `-c:v copy` passthrough, zero-segment fallback.
- ✅ **`orchestrator.py`** — wires everything above into one job, per-stage status updates, `gc.collect()` after large intermediates.
- ✅ **`main.py` + `api/routes.py` + `api/schemas.py`** — FastAPI backend, async job handling via `asyncio.create_task`, in-memory job state.
- ✅ **`config/settings.py`** — central paths, thresholds, `.env` loading.
- ✅ **`app.py`** — light-theme two-column UI, calls the real backend end to end, handles a `failed` state.
- ✅ **Repo structure matches `Architecture.md`** — `src/pipeline/`, `api/`, `config/`, package `__init__.py` files, `requirements.txt` (now includes `torchaudio`, `pix2text`).

**Status:** All four phases are now code-complete. **Nothing has been run end-to-end against a real video yet** — that's the actual next step, not more code.

---

## Which File Is Currently Being Worked On
Just finished `vad_engine.py`, `scene_detector.py`, `ocr_engine.py` — the last three modules `orchestrator.py` needed. Nothing currently in progress.

---

## Next Immediate Step
Run it. `pip install -r requirements.txt`, then `uvicorn main:app --reload` in one terminal and `streamlit run app.py` in another. Upload one real NPTEL video and watch it go through all 7 stages. This is the first real end-to-end test — expect to find and fix issues in threshold tuning (`SILENCE_MIN_SECONDS`, scene-detection `threshold`/`min_gap_seconds`, LLM prompt quality) once real footage is run through it.

---

## Known Issues / Open Questions
- Nothing has been run end-to-end yet — all four phases are code-complete but untested against a real video.
- `scene_detector.py`'s `threshold=0.6` and `min_gap_seconds=1.0` are reasonable starting guesses, not tuned against real NPTEL footage.
- Job state lives in an in-memory dict in `api/routes.py` — fine for local single-user use, will not survive a server restart or scale to concurrent users. Acceptable for current project scope.
- `OCR_ROI_WIDTH`/`OCR_ROI_HEIGHT` (900×450) are a first-pass guess to reduce clipping — still a fixed centered crop, not truly "dynamic" (doesn't detect where the writing actually is on the board). If clipping persists, the real fix is a content-aware crop (e.g. diff against the previous frame to find the changed region) rather than a bigger fixed box.
- Silero VAD downloads via `torch.hub` on first run — needs internet the first time even though it's a local model afterward. Also required `trust_repo=True` to avoid an interactive prompt crashing under uvicorn (fixed 2026-08-06).

---

## Session Log
*(append one entry per work session — do not delete history)*

| Date | Session Summary | Files Touched |
|------|------------------|----------------|
| 2026-08-02 | Set up initial docs (PRD, Architecture, rules, phases, design, memory). Locked in Groq-primary/Gemini-fallback LLM strategy across docs. Built `llm_client.py` with fallback logic. Built standalone minimalistic Streamlit UI (`app.py`) against a mocked pipeline, ready to wire to FastAPI. | PRD.md, Architecture.md, rules.md, phases.md, design.md, memory.md, llm_client.py, app.py |
| 2026-08-02 | Restyled `app.py` with a full-bleed navy gradient hero, orange accent badge/headline, and numbered step cards, inspired by a reference accessibility site screenshot. Functional upload/process/download logic unchanged. | app.py, memory.md |
| 2026-08-02 | Rewrote `app.py` as a two-column dark-theme layout per explicit spec: full-page navy gradient (`.stApp`), left column pitch (badge, orange-accented headline, subtitle, 3-step list), right column glassmorphism card (`st.container(border=True)`, restyled) holding the real uploader/progress/download flow. Functional logic unchanged. | app.py, memory.md |
| 2026-08-02 | Changed left-column 3-step list in `app.py` from explaining internal pipeline stages (Detects Silence / Reads the Board / Speaks it Aloud) to a how-to-use-the-site guide (Upload → We process it automatically → Download the accessible version). | app.py, memory.md |
| 2026-08-02 | Moved the 3-step guide out of the left column into a new full-width "How it Works" section below the two-column row, matching a reference layout: centered badge + orange-accented headline + subtitle, then 3 connected glass cards with large orange numbered circles. | app.py, memory.md |
| 2026-08-02 | Switched `app.py` color theme from dark navy gradient to light (off-white background, dark navy text, white cards with soft border/shadow instead of glassmorphism blur, navy buttons that hover to orange). Layout structure (two-column pitch/tool, How it Works section) unchanged. | app.py, memory.md |
| 2026-08-02 | Built out the remaining pipeline per phases.md: `audio_extractor.py`, `correlator.py`, `tts_client.py`, `muxer.py`, `orchestrator.py`, and the FastAPI backend (`main.py`, `api/routes.py`, `api/schemas.py`, `config/settings.py`). Moved `llm_client.py` into `src/pipeline/`. Rewired `app.py` to call the real backend instead of the mock. Restructured repo to match `Architecture.md` (added `__init__.py` files, `requirements.txt`). Trimmed unnecessary comments across all files. Updated `phases.md` to reflect real completion status — Phase 1 is now the blocker since `orchestrator.py` expects VAD/SBD/OCR modules that haven't been placed in this repo yet. | app.py, src/pipeline/*.py, api/*.py, main.py, config/settings.py, requirements.txt, phases.md, memory.md |
| 2026-08-02 | Wrote `vad_engine.py` (Silero VAD, torch.hub), `scene_detector.py` (8×8 HSV histogram differencing, Hue+Saturation only), and `ocr_engine.py` (Pix2Text, bounded 500×500 ROI crop) — the three modules `orchestrator.py` was waiting on. Function signatures match exactly what the orchestrator calls. Added `torchaudio` and `pix2text` to `requirements.txt`. All four phases are now code-complete; no real end-to-end run yet. | src/pipeline/vad_engine.py, src/pipeline/scene_detector.py, src/pipeline/ocr_engine.py, requirements.txt, phases.md, memory.md |
| 2026-08-06 | First real run hit `EOFError: EOF when reading a line` — `torch.hub.load()` was prompting an interactive trust-repo confirmation that has no stdin under uvicorn. Fixed by passing `trust_repo=True` in `vad_engine.py`. | src/pipeline/vad_engine.py, memory.md |
| 2026-08-06 | Second run hit `Unsupported image type: <class 'numpy.ndarray'>` — Pix2Text's `recognize_formula()` expects a PIL Image, not the raw OpenCV BGR array. Fixed by converting BGR→RGB and wrapping in `Image.fromarray()` before OCR in `ocr_engine.py`. Added `pillow` to `requirements.txt`. | src/pipeline/ocr_engine.py, requirements.txt, memory.md |
| 2026-08-06 | Third run hit `KeyError: 'GROQ_API_KEY'` — `llm_client.py` was reading `os.environ` directly instead of the `.env`-loaded values in `config/settings.py`, so nothing was actually set. Fixed by importing `GROQ_API_KEY`/`GEMINI_API_KEY` from `config.settings`, raising a clear `LLMClientError` instead of a bare `KeyError` if a key is missing, and treating that as a normal fail-over case so it doesn't crash the job. Added `.env.example` as a template. **User still needs to create an actual `.env` with real key values — this fix only makes the failure mode clearer, it doesn't supply the keys.** | src/pipeline/llm_client.py, .env.example, memory.md |
| 2026-08-06 | `.env` still wasn't loading after being created — root cause was `load_dotenv()` in `config/settings.py` being called with no path, so it only searched the current working directory rather than the actual project root. Fixed by calling `load_dotenv(BASE_DIR / ".env")` explicitly. Also added startup warnings that print exactly which `.env` path was checked if a key is still missing, so this is diagnosable next time without guessing. | config/settings.py, memory.md |
| 2026-08-06 | User reported wrong "interpretation" of board text but hadn't isolated where. Added `debug.json` per job (OCR LaTeX + LLM text + provider per segment) so this is inspectable instead of guessed at. User shared a real `debug.json` entry showing malformed OCR output (`\begin{matrix}=\frac{1}{2p} \\ \frac{1}{6}=2H\end{matrix}` — missing left-hand side, two unrelated equations fused) and an LLM description that reversed row order. Root cause was the fixed 500×500 square crop clipping equations that extend past its bounds. Fixed by widening the crop to a configurable 900×450 rectangle (`OCR_ROI_WIDTH`/`OCR_ROI_HEIGHT` in `config/settings.py`). Also rewrote the LLM system prompt to explicitly preserve top-to-bottom row order and describe multi-row matrix content as separate sentences instead of merging them, and bumped `max_tokens`/`maxOutputTokens` from 80→150 to give multi-line descriptions room. | config/settings.py, src/pipeline/ocr_engine.py, src/pipeline/llm_client.py, memory.md |
