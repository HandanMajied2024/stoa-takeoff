"""Build a YOLO detection dataset from CubiCasa annotations.

train split -> train, val split -> val. The test split is never written here: it is our held-out
evaluation set for the benchmark score.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
SRC = Path.home() / "Downloads/cubicasa5k-src/cubicasa5k"
IMAGES = Path.home() / "Downloads/junction-dataset/data/cubicasa5k"
OUT = ROOT / "data_cache" / "yolo_cubicasa"

CLASSES = ["door", "window", "toilet", "sink", "shower", "bathtub", "sauna_stove", "floorplan",
           "bedroom", "kitchen", "bath", "wc_room", "balcony", "sauna_room"]


def classify(o: dict) -> str | None:
    c = o["cls"]
    names = " ".join(o.get("names", [])).upper()
    if c.startswith("Door") and "None" not in c:
        return "door"
    if c.startswith("Window"):
        return "window"
    if c == "FixedFurniture Toilet":
        return "toilet"
    if c.startswith("FixedFurniture") and "Sink" in c:
        return "sink"
    if c == "FixedFurniture Shower":
        return "shower"
    if c == "FixedFurniture Bathtub":
        return "bathtub"
    if "SaunaStove" in c:
        return "sauna_stove"
    if c == "Space Bedroom":
        return "bedroom"
    if c.startswith("Space Kitchen"):
        return "kitchen"
    if c.startswith("Space Outdoor Balcony"):
        return "balcony"
    if c.startswith("Space Sauna"):
        return "sauna_room"
    if c.startswith("Space Bath"):
        return "wc_room" if "WC" in names.split() else "bath"
    return None


def main():
    ann = json.loads((ROOT / "data_cache" / "cubicasa_annotations.json").read_text())
    for split in ("train", "val"):
        (OUT / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT / "labels" / split).mkdir(parents=True, exist_ok=True)
    n = 0
    for key, v in ann.items():
        if v["split"] == "test":
            continue
        img = IMAGES / f"{key}.png"
        if not img.exists():
            continue
        h, w = cv2.imread(str(img), cv2.IMREAD_UNCHANGED).shape[:2]
        # SVG coordinates are in F1_scaled.png pixels; the benchmark image is F1_original.png
        sh, sw = cv2.imread(str(SRC / key.replace("-", "/", 1) / "F1_scaled.png"), cv2.IMREAD_UNCHANGED).shape[:2]
        fx, fy = w / sw, h / sh
        lines = []
        floors: dict[int, list] = {}
        for o in v["objects"]:
            x0, y0, x1, y1 = o["bbox"]
            o["bbox"] = [x0 * fx, y0 * fy, x1 * fx, y1 * fy]
            x0, y0, x1, y1 = o["bbox"]
            floors.setdefault(o["floor"], []).append(o["bbox"])
            cls = classify(o)
            if cls is None:
                continue
            x0, x1 = max(0, x0), min(w, x1)
            y0, y1 = max(0, y0), min(h, y1)
            if x1 - x0 < 2 or y1 - y0 < 2:
                continue
            lines.append(f"{CLASSES.index(cls)} {(x0 + x1) / 2 / w:.6f} {(y0 + y1) / 2 / h:.6f} {(x1 - x0) / w:.6f} {(y1 - y0) / h:.6f}")
        for boxes in floors.values():  # one box per drawn floor plan
            x0 = max(0, min(b[0] for b in boxes)); y0 = max(0, min(b[1] for b in boxes))
            x1 = min(w, max(b[2] for b in boxes)); y1 = min(h, max(b[3] for b in boxes))
            lines.append(f"{CLASSES.index('floorplan')} {(x0 + x1) / 2 / w:.6f} {(y0 + y1) / 2 / h:.6f} {(x1 - x0) / w:.6f} {(y1 - y0) / h:.6f}")
        split = v["split"]
        dst = OUT / "images" / split / f"{key}.png"
        if not dst.exists():
            os.symlink(img, dst)
        (OUT / "labels" / split / f"{key}.txt").write_text("\n".join(lines))
        n += 1
    (OUT / "data.yaml").write_text(
        f"path: {OUT}\ntrain: images/train\nval: images/val\nnames:\n" + "".join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES)))
    print(n, "images written to", OUT)


if __name__ == "__main__":
    main()
