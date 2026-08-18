from pathlib import Path

import cv2


def detect_scene_changes(video_path: Path, threshold: float = 0.6,
                          min_gap_seconds: float = 1.0) -> list[float]:
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    scene_changes = []
    prev_hist = None
    last_change = -min_gap_seconds
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [8, 8], [0, 180, 0, 256])
        cv2.normalize(hist, hist)

        if prev_hist is not None:
            similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
            timestamp = frame_idx / fps
            if similarity < threshold and timestamp - last_change >= min_gap_seconds:
                scene_changes.append(timestamp)
                last_change = timestamp

        prev_hist = hist
        frame_idx += 1

    cap.release()
    return scene_changes
