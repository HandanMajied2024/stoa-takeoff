"""OCR for raster floor plans: read every text label in all four orientations and map the results
back to original image coordinates, then deduplicate. Plans are often scanned sideways or upside down,
and labels can be vertical, so one orientation is never enough."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

CACHE = Path(__file__).resolve().parents[2] / "data_cache" / "ocr"


@lru_cache(maxsize=1)
def _engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)


def _unrotate(pts: np.ndarray, rot: int, w: int, h: int, scale: float) -> np.ndarray:
    """Map points from a rotated+scaled image back to original pixel coords."""
    p = pts / scale
    if rot == 0:
        return p
    if rot == 90:    # cv2.ROTATE_90_CLOCKWISE: (x,y) -> (h-1-y, x)
        return np.c_[p[:, 1], h - 1 - p[:, 0]]
    if rot == 180:
        return np.c_[w - 1 - p[:, 0], h - 1 - p[:, 1]]
    if rot == 270:   # counter-clockwise
        return np.c_[w - 1 - p[:, 1], p[:, 0]]
    raise ValueError(rot)


# 0 and 90 are enough: the OCR angle classifier already reads upside-down (180/270) text.
ROT = {0: None, 90: cv2.ROTATE_90_CLOCKWISE}


def read_tokens(path: str | Path, scale: float = 2.0, use_cache: bool = True) -> list[dict]:
    path = Path(path)
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / f"{path.stem}.json"
    if use_cache and cached.exists():
        return json.loads(cached.read_text())
    img = cv2.imread(str(path))
    h, w = img.shape[:2]
    scale = min(scale, 2400 / max(h, w)) if max(h, w) * scale > 2400 else scale  # big scans: no upscaling blow-up
    toks = []
    for rot, code in ROT.items():
        x = img if code is None else cv2.rotate(img, code)
        x = cv2.resize(x, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        res, _ = _engine()(x)
        for box, text, conf in res or []:
            pts = _unrotate(np.array(box, dtype=float), rot, w, h, scale)
            toks.append({"text": text.strip(), "conf": float(conf), "rot": rot,
                         "box": [float(pts[:, 0].min()), float(pts[:, 1].min()), float(pts[:, 0].max()), float(pts[:, 1].max())]})
    toks = _dedupe(toks)
    cached.write_text(json.dumps(toks, ensure_ascii=False))
    return toks


def _iou(a, b) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / u if u > 0 else 0.0


def _dedupe(toks: list[dict]) -> list[dict]:
    """Same label read in several orientations -> keep the most confident reading."""
    toks = sorted(toks, key=lambda t: -t["conf"])
    keep: list[dict] = []
    for t in toks:
        if all(_iou(t["box"], k["box"]) < 0.3 for k in keep):
            keep.append(t)
    return keep


def _safe(p):
    try:
        read_tokens(p)
    except Exception as ex:  # one bad scan must not stop the batch
        print("FAILED", p, ex, flush=True)


if __name__ == "__main__":
    import sys
    from concurrent.futures import ProcessPoolExecutor

    files = [f for f in sorted(Path(sys.argv[1]).glob("*.png")) if not (CACHE / f"{f.stem}.json").exists()]
    with ProcessPoolExecutor(int(sys.argv[2]) if len(sys.argv) > 2 else 8, max_tasks_per_child=50) as ex:
        for i, _ in enumerate(ex.map(_safe, files, chunksize=4), 1):
            if i % 250 == 0:
                print(i, "/", len(files), flush=True)
