import gc
from pathlib import Path
from typing import Optional

import cv2
from PIL import Image
from pix2text import Pix2Text

from config.settings import OCR_ROI_WIDTH, OCR_ROI_HEIGHT

_model = None


def _load_model():
    global _model
    if _model is None:
        _model = Pix2Text.from_config()
    return _model


def _crop_roi(frame, roi_width: int = OCR_ROI_WIDTH, roi_height: int = OCR_ROI_HEIGHT):
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    x1 = max(0, cx - roi_width // 2)
    y1 = max(0, cy - roi_height // 2)
    x2 = min(w, x1 + roi_width)
    y2 = min(h, y1 + roi_height)
    x1 = max(0, x2 - roi_width)
    y1 = max(0, y2 - roi_height)

    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]


def extract_latex_at_timestamp(video_path: Path, timestamp: float,
                                roi_width: int = OCR_ROI_WIDTH,
                                roi_height: int = OCR_ROI_HEIGHT) -> Optional[str]:
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    crop = _crop_roi(frame, roi_width, roi_height)
    del frame
    if crop is None:
        return None

    model = _load_model()
    pil_crop = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    result = model.recognize_formula(pil_crop)
    del crop, pil_crop
    gc.collect()

    if not result:
        return None
    return result.strip()
