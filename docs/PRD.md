# Project Requirements Document (PRD)
## Automated Audio Description System for NPTEL Lectures

### 1. Project Definition
We are building an **offline-first, edge-optimized accessibility pipeline** that automatically generates spoken audio descriptions of blackboard mathematics during silent instructional pauses in NPTEL lecture videos. The system detects when an instructor stops speaking, identifies whether a scene change (new board content) occurred, extracts the mathematical content via OCR, converts it to natural language via an LLM, synthesizes speech, and muxes the result back into the original video — without requiring GPU hardware or heavy local models.

This is **not** a general video-accessibility tool. It is purpose-built for the specific visual/audio grammar of NPTEL-style lectures: static camera, blackboard/whiteboard content, and instructor pauses while writing.

### 2. Problem Statement
Visually impaired and blind students cannot access the mathematical content written on the board during an NPTEL lecture — only the instructor's spoken narration, which frequently lags behind or omits what is written. Existing solutions (full ASR + manual captioning, human audio-description services) are expensive, non-scalable, or hardware-prohibitive for institutions with limited compute budgets.

### 3. Target Users
- **Primary:** Visually impaired / blind engineering and science students using NPTEL for coursework.
- **Secondary:** Auditory learners who benefit from redundant verbal description of visual math content.
- **Tertiary:** Educational institutions (like CDAC) seeking to retrofit accessibility onto large existing NPTEL video libraries without expensive infrastructure.

### 4. Hardware Constraint (Non-Negotiable)
The entire backend pipeline must run on a **standard laptop with exactly 6GB of RAM**. This constraint governs every architectural decision downstream. No component may load a model that risks exceeding this ceiling in combination with the OS, Python runtime, and other pipeline stages running concurrently or sequentially.

### 5. Core Features / Scope

| # | Feature | Module | Status |
|---|---------|--------|--------|
| 1 | Silence/pause detection in lecture audio | VAD (Silero) | ✅ Verified |
| 2 | Detection of board-content scene changes | SBD (OpenCV HSV Histogram) | ✅ Verified |
| 3 | Extraction of LaTeX from board frames | Spatial Math OCR (Pix2Text) | ✅ Verified |
| 4 | Translation of LaTeX → natural spoken English | LLM API (Groq/Llama 3 or Gemini) | 🔲 Pending |
| 5 | Text-to-speech audio generation | TTS API (Edge-TTS) | 🔲 Pending |
| 6 | Stitching TTS audio into silent gaps of original video | Media Muxing (FFmpeg CLI) | 🔲 Pending |
| 7 | User-facing upload/processing dashboard | Streamlit Frontend | 🔲 Pending |
| 8 | Async orchestration of the above pipeline | FastAPI Backend | 🔲 Pending |

### 6. Explicit Out-of-Scope (to protect RAM budget and project focus)
- Full-video ASR/transcription (Whisper, Vosk, etc.) — not needed since we target *silence*, not speech.
- Local LLM inference (Llama.cpp, GGUF models, etc.) — replaced entirely by cloud API calls.
- Real-time/live processing — this is a batch, offline-video pipeline.
- Multi-language TTS/translation — English-only for v1.
- Handwriting style transfer, board content "beautification," or diagram redrawing.

### 7. Success Criteria
- Pipeline processes a 60-minute NPTEL lecture end-to-end on a 6GB RAM machine without OOM failure.
- Generated audio descriptions are inserted only within detected silence windows ≥1.5s, without overlapping instructor speech.
- OCR→LLM→TTS latency per detected math segment is acceptable for batch (non-real-time) processing.
- Final muxed video plays correctly in standard video players with synced audio description tracks.

### 8. Assumptions
- Reliable internet connectivity is available during processing (required for LLM/TTS API calls).
- Source videos are static-camera, blackboard/whiteboard-style NPTEL recordings (not high-motion or multi-camera).
- API costs (Groq/Gemini, Edge-TTS is free) are acceptable for the target scale of use.
