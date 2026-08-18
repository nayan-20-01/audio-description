import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AudioClip:
    start_seconds: float
    file_path: Path


def mux_segments(video_path: Path, clips: list[AudioClip], output_path: Path) -> Path:
    if not clips:
        cmd = ["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg passthrough failed: {result.stderr}")
        return output_path

    inputs = ["-i", str(video_path)]
    for clip in clips:
        inputs += ["-i", str(clip.file_path)]

    filter_parts = []
    mix_labels = ["0:a"]
    for i, clip in enumerate(clips, start=1):
        delay_ms = int(clip.start_seconds * 1000)
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")
        mix_labels.append(f"a{i}")

    mix_inputs = "".join(f"[{label}]" for label in mix_labels)
    filter_parts.append(f"{mix_inputs}amix=inputs={len(mix_labels)}:duration=first[aout]")
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg muxing failed: {result.stderr}")
    return output_path
