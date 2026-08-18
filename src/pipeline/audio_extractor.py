import subprocess
from pathlib import Path


def extract_audio(video_path: Path, output_dir: Path) -> Path:
    output_path = output_dir / f"{video_path.stem}.wav"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr}")
    return output_path
