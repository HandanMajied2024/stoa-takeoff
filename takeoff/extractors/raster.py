"""Raster floor plans (scans / images): symbol detector + OCR -> Building.

The detector finds doors, windows, sanitary fixtures, sauna stoves, room extents and separate floor
plans on the sheet. OCR reads the room labels (MH, KPH, WC, S, PARVEKE...) and is attached as
independent evidence: when the label disagrees with the detected room type, the room is flagged
for a human instead of silently trusted.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..model import Building, Element, Source
from . import fi_labels

ROOT = Path(__file__).resolve().parents[2]
WEIGHTS = ROOT / "models" / "cubicasa_symbols.pt"
DET_CACHE = ROOT / "data_cache" / "detections"
THRESH_FILE = ROOT / "models" / "cubicasa_thresholds.json"

FIXTURE = {"toilet": "wc", "sink": "sink", "shower": "shower", "bathtub": "bathtub", "sauna_stove": "sauna_stove"}
ROOM = {"bedroom": "bedroom", "kitchen": "kitchen", "bath": "bathroom", "wc_room": "wc", "balcony": "balcony",
        "sauna_room": "sauna"}
DEFAULT_THRESH = 0.35


@lru_cache(maxsize=1)
def _model():
    from ultralytics import YOLO
    return YOLO(str(WEIGHTS))


@lru_cache(maxsize=1)
def thresholds() -> dict:
    return json.loads(THRESH_FILE.read_text()) if THRESH_FILE.exists() else {}


def detect(path: Path, use_cache: bool = True) -> list[dict]:
    """All detections down to conf 0.05 (thresholds are applied later, so they can be tuned)."""
    st = WEIGHTS.stat()
    cache_dir = DET_CACHE / f"{st.st_size}-{int(st.st_mtime)}"  # new weights -> new cache
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{path.stem}.json"
    if use_cache and cached.exists():
        return json.loads(cached.read_text())
    r = _model().predict(str(path), imgsz=1024, conf=0.05, iou=0.5, verbose=False, max_det=600)[0]
    names = r.names
    dets = [{"cls": names[int(c)], "conf": float(s), "box": [float(x) for x in b]}
            for b, s, c in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist(), r.boxes.cls.tolist())]
    cached.write_text(json.dumps(dets))
    return dets


def _inside(box, pt) -> bool:
    return box[0] <= pt[0] <= box[2] and box[1] <= pt[1] <= box[3]


def extract(path: str | Path) -> Building:
    path = Path(path)
    src = str(path)
    th = thresholds()
    dets = [d for d in detect(path) if d["conf"] >= th.get(d["cls"], DEFAULT_THRESH)]
    b = Building(id=path.stem, source_file=src, source_type="raster")

    try:
        from .raster_ocr import read_tokens
        toks = [t for t in read_tokens(path) if t["conf"] >= 0.6]
    except Exception:
        toks = []
        b.flags.append("OCR unavailable: room labels not cross-checked")

    def el(i, d, kind, subtype=None, name=None):
        x0, y0, x1, y1 = d["box"]
        flags = [] if d["conf"] >= 0.6 else [f"low detector confidence {d['conf']:.2f}"]
        return Element(id=f"{d['cls']}-{i}", kind=kind, subtype=subtype, name=name,
                       polygon=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)], confidence=round(d["conf"], 3), flags=flags,
                       source=Source(file=src, ref=f"bbox:{x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}", method="yolo.symbols"))

    floors = [d for d in dets if d["cls"] == "floorplan"]
    for i, d in enumerate(floors or [{"cls": "floorplan", "conf": 0.5, "box": [0, 0, 0, 0]}]):
        e = el(i, d, "floor")
        if not floors:
            e.flags.append("no floor outline detected: assumed one floor")
        b.elements.append(e)
    b.levels = [f"floor {i + 1}" for i in range(max(1, len(floors)))]

    stoves = 0
    sauna_rooms = []
    for i, d in enumerate(dets):
        c = d["cls"]
        if c == "door":
            b.elements.append(el(i, d, "door"))
        elif c == "window":
            b.elements.append(el(i, d, "window"))
        elif c in FIXTURE:
            if c == "sauna_stove":
                stoves += 1
            b.elements.append(el(i, d, "fixture", FIXTURE[c]))
        elif c in ROOM:
            labels = [t["text"] for t in toks
                      if _inside(d["box"], ((t["box"][0] + t["box"][2]) / 2, (t["box"][1] + t["box"][3]) / 2))]
            e = el(i, d, "room", ROOM[c], name=" ".join(labels) or None)
            said = {rt for lab in labels for rt in fi_labels.room_types(lab)}
            if said and ROOM[c] not in said and not (said & {"room", "living", "utility"}):
                e.flags.append(f"label {labels} suggests {sorted(said)}, detector says {ROOM[c]}")
                e.confidence = min(e.confidence, 0.5)
            if c == "sauna_room":
                sauna_rooms.append(e)
            else:
                b.elements.append(e)

    # a sauna is a sauna room or a stove (annotators mark the stove even when the room is untyped)
    b.elements.extend(sauna_rooms)
    for j in range(max(0, stoves - len(sauna_rooms))):
        b.elements.append(Element(id=f"sauna-from-stove-{j}", kind="room", subtype="sauna", confidence=0.8,
                                  flags=["sauna inferred from a sauna stove"],
                                  source=Source(file=src, method="yolo.symbols+rule")))
    b.meta["ocr_labels"] = [t["text"] for t in toks][:200]
    return b
