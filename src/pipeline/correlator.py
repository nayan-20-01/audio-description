from dataclasses import dataclass


@dataclass
class MatchedSegment:
    silence_start: float
    silence_end: float
    scene_time: float


def correlate(silences: list[tuple[float, float]], scene_changes: list[float],
              tolerance: float = 2.0) -> list[MatchedSegment]:
    matched = []
    for start, end in silences:
        candidates = [t for t in scene_changes if start - tolerance <= t <= end + tolerance]
        if not candidates:
            continue
        closest = min(candidates, key=lambda t: abs(t - start))
        matched.append(MatchedSegment(silence_start=start, silence_end=end, scene_time=closest))
    return matched
