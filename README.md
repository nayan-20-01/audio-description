# NPTEL Audio Description

Automatically narrates board equations during silent pauses in NPTEL lecture videos, so visually impaired and auditory learners never miss what's written on the board.

## How it works

1. **Detects silence** — Silero VAD finds pauses over 1.5s where the instructor stops speaking.
2. **Detects board changes** — a custom 64-bin HSV histogram differencing algorithm (Hue + Saturation only, ignoring Value to defeat glare) finds when the board content changes.
3. **Reads the board** — Pix2Text OCR extracts LaTeX from a cropped region of the frame at each detected change.
4. **Describes it** — Groq (`llama-3.1-8b-instant`, primary) or Gemini (`gemini-2.0-flash`, fallback) converts the LaTeX into a spoken English sentence.
5. **Speaks it** — Edge-TTS synthesizes the description, fitted to the length of the silence window.
6. **Assembles the video** — FFmpeg mixes the generated audio into the original track at the right timestamps.

## Stack

| Layer | Tech |
|---|---|
| VAD | Silero VAD |
| Scene detection | OpenCV (custom HSV histogram) |
| OCR | Pix2Text |
| LLM | Groq (primary) / Gemini (fallback) |
| TTS | Edge-TTS |
| Muxing | FFmpeg |
| Backend | FastAPI |
| Frontend | Streamlit |

See `docs/Architecture.md` for the full pipeline diagram and folder structure, `docs/rules.md` for what's in/out of scope, and `docs/phases.md` for current build status.

## Setup

```bash
git clone <this-repo-url>
cd nptel-audio-description
pip install -r requirements.txt
cp .env.example .env   # fill in GROQ_API_KEY and GEMINI_API_KEY
```

FFmpeg must also be installed on the system separately (`apt install ffmpeg` / `brew install ffmpeg`).

## Running

```bash
uvicorn main:app --reload
```

In a second terminal:

```bash
streamlit run app.py
```

Upload a lecture video in the Streamlit UI at `localhost:8501`; it calls the FastAPI backend at `localhost:8000`.

## Project status

Code-complete across all four build phases; tested against real NPTEL footage with several fixes applied along the way (see `docs/memory.md` for the running development log). OCR crop size and scene-detection thresholds are still being tuned against real board content.
