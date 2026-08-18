import logging
from pathlib import Path

import edge_tts

logger = logging.getLogger("tts_client")

DEFAULT_VOICE = "en-IN-NeerjaNeural"


async def synthesize(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> Path:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    return output_path


async def get_audio_duration_seconds(audio_path: Path) -> float:
    import subprocess
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


async def synthesize_fitted(text: str, output_path: Path, max_duration_seconds: float,
                             voice: str = DEFAULT_VOICE) -> Path:
    await synthesize(text, output_path, voice)
    duration = await get_audio_duration_seconds(output_path)
    if duration <= max_duration_seconds:
        return output_path

    words = text.split()
    while duration > max_duration_seconds and len(words) > 3:
        words = words[: int(len(words) * 0.8)]
        shortened = " ".join(words) + "."
        await synthesize(shortened, output_path, voice)
        duration = await get_audio_duration_seconds(output_path)

    if duration > max_duration_seconds:
        logger.warning("Could not fit description into %.1fs window", max_duration_seconds)
    return output_path
