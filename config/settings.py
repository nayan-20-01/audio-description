import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RAW_DIR = BASE_DIR / "data" / "raw"
INTERMEDIATE_DIR = BASE_DIR / "data" / "intermediate"
OUTPUT_DIR = BASE_DIR / "data" / "output"

for d in (RAW_DIR, INTERMEDIATE_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GROQ_API_KEY:
    print(f"WARNING: GROQ_API_KEY not set — checked {BASE_DIR / '.env'}")
if not GEMINI_API_KEY:
    print(f"WARNING: GEMINI_API_KEY not set — checked {BASE_DIR / '.env'}")

SILENCE_MIN_SECONDS = 1.5
SCENE_MATCH_TOLERANCE_SECONDS = 2.0
TTS_VOICE = "en-IN-NeerjaNeural"
MAX_UPLOAD_MB = 200
OCR_ROI_WIDTH = 900
OCR_ROI_HEIGHT = 450
