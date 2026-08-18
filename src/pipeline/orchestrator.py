import gc
import json
import logging
from pathlib import Path

from src.pipeline.audio_extractor import extract_audio
from src.pipeline.correlator import correlate
from src.pipeline.llm_client import latex_to_speech_text, LLMClientError
from src.pipeline.tts_client import synthesize_fitted
from src.pipeline.muxer import mux_segments, AudioClip

# vad_engine, scene_detector, ocr_engine are pre-existing verified modules
from src.pipeline.vad_engine import detect_silences
from src.pipeline.scene_detector import detect_scene_changes
from src.pipeline.ocr_engine import extract_latex_at_timestamp

from config.settings import (
    SILENCE_MIN_SECONDS,
    SCENE_MATCH_TOLERANCE_SECONDS,
    INTERMEDIATE_DIR,
    OUTPUT_DIR,
)

logger = logging.getLogger("orchestrator")

STAGES = [
    "extracting_audio",
    "detecting_silence",
    "detecting_scenes",
    "reading_board",
    "generating_descriptions",
    "synthesizing_audio",
    "assembling_video",
]


async def run_pipeline(video_path: Path, job_id: str, jobs: dict) -> Path:
    job_dir = INTERMEDIATE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    debug_log = []

    jobs[job_id]["stage"] = "extracting_audio"
    audio_path = extract_audio(video_path, job_dir)

    jobs[job_id]["stage"] = "detecting_silence"
    silences = detect_silences(audio_path, min_duration=SILENCE_MIN_SECONDS)
    del audio_path
    gc.collect()

    jobs[job_id]["stage"] = "detecting_scenes"
    scene_changes = detect_scene_changes(video_path)

    matches = correlate(silences, scene_changes, tolerance=SCENE_MATCH_TOLERANCE_SECONDS)
    del silences, scene_changes
    gc.collect()

    jobs[job_id]["stage"] = "reading_board"
    segments = []
    for match in matches:
        latex = extract_latex_at_timestamp(video_path, match.scene_time)
        debug_log.append({"scene_time": match.scene_time, "ocr_latex": latex})
        if latex:
            segments.append({"match": match, "latex": latex})

    jobs[job_id]["stage"] = "generating_descriptions"
    clips: list[AudioClip] = []
    for i, seg in enumerate(segments):
        entry = next(d for d in debug_log if d["scene_time"] == seg["match"].scene_time)
        try:
            result = await latex_to_speech_text(seg["latex"])
        except LLMClientError as exc:
            logger.error("Segment %d skipped: %s", i, exc)
            entry["llm_error"] = str(exc)
            continue

        entry["llm_provider"] = result.provider
        entry["llm_text"] = result.text

        clip_path = job_dir / f"clip_{i}.mp3"
        window_seconds = seg["match"].silence_end - seg["match"].silence_start
        await synthesize_fitted(result.text, clip_path, window_seconds)
        clips.append(AudioClip(start_seconds=seg["match"].silence_start, file_path=clip_path))

    (job_dir / "debug.json").write_text(json.dumps(debug_log, indent=2))

    jobs[job_id]["stage"] = "assembling_video"
    output_path = OUTPUT_DIR / f"{job_id}.mp4"
    mux_segments(video_path, clips, output_path)

    jobs[job_id]["segments_generated"] = len(clips)
    jobs[job_id]["audio_added_seconds"] = sum(
        seg["match"].silence_end - seg["match"].silence_start for seg in segments
    )
    return output_path
