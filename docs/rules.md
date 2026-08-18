# Development Rules & Boundaries
## NPTEL Audio Description Pipeline

### 1. What to Use (Approved Stack)
- **Video/Audio processing:** FFmpeg (CLI via subprocess) — extraction, muxing, format conversion
- **VAD:** Silero VAD only
- **Scene/Shot Boundary Detection:** OpenCV (`cv2`) with the existing custom HSV histogram differencing algorithm
- **OCR:** Pix2Text, always with bounded ROI cropping (never full-frame inference)
- **LLM:** Groq API (`llama-3.1-8b-instant`) as primary — fastest inference, ~14,400 requests/day free tier, no credit card required. Google Gemini API (`gemini-2.0-flash`) as automatic fallback — lower daily request cap (~1,500/day) but much higher tokens-per-minute headroom (~1M TPM vs Groq's ~6K TPM), used when Groq returns a 429 (rate limit) response. Both cloud-hosted, both free-tier, zero local RAM cost
- **TTS:** Edge-TTS (Microsoft), async calls only
- **Backend:** FastAPI (async endpoints, Pydantic schemas)
- **Frontend:** Streamlit
- **Config/secrets:** `.env` + `python-dotenv`, never hardcoded API keys

### 2. What to Avoid (Strictly Forbidden)
- ❌ **Whisper (any variant, including whisper.cpp)** — full ASR is out of scope; VAD handles silence detection, not transcription
- ❌ **Any local LLM inference** (Llama.cpp, GGUF/GGML models, Ollama, local Llama/Mistral/Phi weights) — LLM work is API-only
- ❌ **Heavy local vision models** for scene detection (no CNN-based shot boundary detectors, no YOLO, no deep embedding comparisons) — the HSV histogram method is final and sufficient
- ❌ **Heavy UI frameworks** (Electron, Django+React, Node-based SPAs) — Streamlit is the sole frontend
- ❌ **In-memory full-video loading** (e.g., loading an entire video into a numpy array) — always stream/process frame-by-frame or via FFmpeg subprocess
- ❌ **Synchronous blocking API calls** on the FastAPI event loop — all LLM/TTS calls must be async
- ❌ **GPU-dependent libraries** — this project assumes CPU-only hardware at all times

### 3. Error Handling Rules
- Every pipeline stage (`vad_engine`, `scene_detector`, `ocr_engine`, `llm_client`, `tts_client`, `muxer`) must be a **pure, isolated function** with explicit try/except boundaries — a failure in one stage must not crash the whole job.
- On API failure (Groq/Gemini/Edge-TTS), retry with exponential backoff (max 3 attempts) before marking that segment as failed and continuing the pipeline for remaining segments — one bad segment should never kill the whole job.
- **LLM provider fallback:** `llm_client.py` must call Groq (`llama-3.1-8b-instant`) first. On a `429` (rate limit) or timeout, automatically retry the same request against Gemini (`gemini-2.0-flash`) before giving up. Only mark a segment as failed if both providers are exhausted. Never let a Groq per-minute throttle stall the whole batch — fail over immediately rather than sleeping and retrying the same provider repeatedly.
- All OCR crops must validate ROI bounds before slicing the frame array (already implemented — preserve this pattern in any new code touching frames).
- Log every stage transition with job_id, timestamp, and stage name to `logs/` for debuggability without needing to re-run the full pipeline.
- Never fail silently — any skipped segment (e.g., silence window with no OCR match) must be logged as "skipped: reason" not just dropped.

### 4. Memory-Safety Boundaries for AI-Assisted Development
- When asking an AI assistant (Claude, Copilot, etc.) to write code for this project, **explicitly restate the 6GB RAM constraint and the forbidden-library list in the prompt** — do not assume it will remember from a prior session.
- Any suggested library must be checked against "What to Avoid" above before adoption.
- New modules must include an explicit memory-release step (`gc.collect()`, closing file handles, releasing cv2 frame buffers) at the end of their function scope.
- Prefer disk-based intermediate storage (temp files) over holding large objects in memory across stage boundaries.
- Any code review pass should include a "does this introduce a hidden heavy dependency?" check (e.g., a library that pulls in `torch` + a large pretrained model transitively).

### 5. Scope Discipline
- No feature work outside the 8 core features listed in `PRD.md` without updating the PRD first.
- Resist scope creep toward real-time processing, multi-language support, or non-NPTEL video formats until v1 is stable and verified end-to-end.
