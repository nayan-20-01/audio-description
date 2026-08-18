import gc
from pathlib import Path

import torch

_model = None
_utils = None


def _load_model():
    global _model, _utils
    if _model is None:
        torch.set_num_threads(1)
        _model, _utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            trust_repo=True,
        )
    return _model, _utils


def detect_silences(audio_path: Path, min_duration: float = 1.5) -> list[tuple[float, float]]:
    model, utils = _load_model()
    get_speech_timestamps, _, read_audio, *_ = utils

    wav = read_audio(str(audio_path), sampling_rate=16000)
    total_duration = len(wav) / 16000

    speech_segments = get_speech_timestamps(
        wav, model, sampling_rate=16000, return_seconds=True
    )
    del wav
    gc.collect()

    silences = []
    cursor = 0.0
    for seg in speech_segments:
        gap = seg["start"] - cursor
        if gap >= min_duration:
            silences.append((cursor, seg["start"]))
        cursor = seg["end"]

    if total_duration - cursor >= min_duration:
        silences.append((cursor, total_duration))

    return silences
