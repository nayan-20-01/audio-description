# System Architecture
## NPTEL Automated Audio Description — Edge-Optimized Pipeline

### 1. High-Level App Flow

```
[1] Video Upload (Streamlit UI)
        |
        v
[2] FastAPI receives file, stores to /data/raw, creates job_id
        |
        v
[3] Audio Extraction (FFmpeg: video -> mono 16kHz WAV)
        |
        v
[4] VAD Pass (Silero) --> list of silence windows [(start, end), ...] > 1.5s
        |
        v
[5] SBD Pass (OpenCV HSV Histogram Diff) --> list of scene-change timestamps
        |
        v
[6] Correlation Step --> match silence windows to nearby scene changes
        (a silence window with no board change = skip, no description needed)
        |
        v
[7] Frame Extraction --> grab representative frame(s) at each matched scene change
        |
        v
[8] Spatial Math OCR (Pix2Text, 500x500 dynamic ROI crop) --> LaTeX string(s)
        |
        v
[9] LLM API Call (Groq llama-3.1-8b-instant primary, Gemini 2.0 Flash fallback on 429) --> LaTeX to natural spoken English
        |
        v
[10] TTS API Call (Edge-TTS, async) --> generates .mp3/.wav clip per description
        |
        v
[11] Duration Check --> trim/pace description to fit within the silence window
        |
        v
[12] FFmpeg Muxing --> overlay/insert TTS clips into original audio track at correct timestamps
        |
        v
[13] Final Video Assembly --> re-mux video + modified audio track
        |
        v
[14] Output stored in /data/output, job marked complete, Streamlit polls FastAPI and shows download link
```

### 2. Proposed Folder & File Structure

```
nptel-audio-description/
│
├── app.py                        # Streamlit entrypoint (UI only, no heavy logic)
├── main.py                       # FastAPI entrypoint (uvicorn app)
│
├── api/
│   ├── __init__.py
│   ├── routes.py                 # FastAPI route definitions (/upload, /status, /download)
│   └── schemas.py                # Pydantic request/response models
│
├── src/
│   ├── __init__.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Runs the full pipeline sequence, job state machine
│   │   ├── audio_extractor.py    # FFmpeg wrapper: video -> wav
│   │   ├── vad_engine.py         # Silero VAD wrapper (verified module)
│   │   ├── scene_detector.py     # OpenCV HSV histogram SBD (verified module)
│   │   ├── ocr_engine.py         # Pix2Text wrapper with ROI cropping (verified module)
│   │   ├── correlator.py         # Matches silence windows <-> scene changes
│   │   ├── llm_client.py         # Groq/Gemini API wrapper (LaTeX -> English)
│   │   ├── tts_client.py         # Edge-TTS async wrapper
│   │   └── muxer.py              # FFmpeg audio insertion + final video assembly
│   │
│   └── utils/
│       ├── __init__.py
│       ├── memory_utils.py       # Explicit gc.collect() / model unload helpers
│       ├── file_utils.py         # Temp file management, cleanup
│       ├── timestamp_utils.py    # Time window math, overlap checks
│       └── logger.py             # Structured logging (per-job, per-stage)
│
├── config/
│   └── settings.py                # Central config: thresholds, API keys (from .env), paths
│
├── data/
│   ├── raw/                       # Uploaded source videos
│   ├── intermediate/              # Extracted audio, frames, temp TTS clips
│   └── output/                    # Final muxed videos
│
├── tests/
│   ├── test_vad_engine.py
│   ├── test_scene_detector.py
│   ├── test_ocr_engine.py
│   └── test_pipeline_integration.py
│
├── docs/
│   ├── PRD.md
│   ├── Architecture.md
│   ├── rules.md
│   ├── phases.md
│   ├── design.md
│   └── memory.md
│
├── .env                            # GROQ_API_KEY / GEMINI_API_KEY (gitignored)
├── requirements.txt
└── README.md
```

### 3. Tech Stack & RAM-Protection Rationale

| Layer | Technology | Why It Protects the 6GB Ceiling |
|---|---|---|
| VAD | Silero VAD (~2MB PyTorch) | Tiny model, loads/unloads in milliseconds; no GPU dependency |
| Scene Detection | OpenCV (cv2) + custom HSV histogram | Pure CPU array math, no neural network, no persistent model in memory |
| OCR | Pix2Text with 500x500 ROI cropping | Cropping the frame before inference caps the tensor size fed to the model, avoiding full-frame memory spikes |
| LLM | Groq API (`llama-3.1-8b-instant`, primary) + Gemini API (`gemini-2.0-flash`, fallback) | Zero local RAM cost — inference happens remotely; only lightweight HTTP request/response objects held in memory. Dual-provider fallback maximizes free-tier headroom: Groq's high daily request cap covers normal volume, Gemini's high per-minute token cap absorbs bursts without paying for either |
| TTS | Edge-TTS (Microsoft, cloud-based) | Zero local model weights; async streaming keeps memory footprint to network buffers only |
| Muxing | FFmpeg CLI (subprocess) | Operates as an external OS process, not in-Python-memory; streams rather than loading full video into RAM |
| Backend | FastAPI (async) | Lightweight ASGI framework; async I/O means API/TTS calls don't block or duplicate memory across threads |
| Frontend | Streamlit | Minimal framework overhead vs. heavier options (Electron/Node-based UIs); runs as a separate lightweight process from the backend |

### 4. Memory Discipline Principles
- Each pipeline stage runs as an **isolated function/process** — load what's needed, process, explicitly release (`del`, `gc.collect()`), move to next stage.
- No two heavy stages should hold their working data in memory simultaneously if avoidable — write intermediate artifacts (extracted audio, cropped frames, LaTeX text) to disk between stages.
- FFmpeg operations are always subprocess calls, never in-memory video buffer manipulation.
- API calls (LLM, TTS) are stateless from the pipeline's perspective — no client-side model state retained between calls.
