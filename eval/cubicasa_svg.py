"""Parse CubiCasa5k model.svg annotations into objects with pixel bounding boxes.

Training data tooling only: the product never sees these SVGs at inference time. We only use the
official TRAIN split for training/calibration and report scores on the held-out TEST split.
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

NS = "{http://www.w3.org/2000/svg}"
MATRIX = re.compile(r"matrix\(([^)]+)\)")
TOP_PREFIXES = ("Space ", "Door", "Window", "FixedFurniture ", "Stairs", "Railing", "Wall", "Column")
SRC = Path.home() / "Downloads/cubicasa5k-src/cubicasa5k"


def _mat(t: str | None) -> np.ndarray:
    m = np.eye(3)
    if t and (g := MATRIX.search(t)):
        a, b, c, d, e, f = [float(x) for x in re.split(r"[ ,]+", g.group(1).strip())]
        m = np.array([[a, c, e], [b, d, f], [0, 0, 1]])
    return m


def _points(el) -> np.ndarray | None:
    tag = el.tag.replace(NS, "")
    if tag == "polygon" or tag == "polyline":
        nums = [float(x) for x in re.split(r"[ ,]+", el.get("points", "").strip()) if x]
        return np.array(nums).reshape(-1, 2) if len(nums) >= 4 else None
    if tag == "rect":
        x, y, w, h = (float(el.get(k, 0)) for k in ("x", "y", "width", "height"))
        return np.array([[x, y], [x + w, y + h]])
    if tag == "line":
        return np.array([[float(el.get("x1", 0)), float(el.get("y1", 0))], [float(el.get("x2", 0)), float(el.get("y2", 0))]])
    if tag in ("circle", "ellipse"):
        cx, cy = float(el.get("cx", 0)), float(el.get("cy", 0))
        rx = float(el.get("r", el.get("rx", 0)))
        ry = float(el.get("r", el.get("ry", 0)))
        return np.array([[cx - rx, cy - ry], [cx + rx, cy + ry]])
    return None


def _collect(el, m, out, hidden=False):
    m = m @ _mat(el.get("transform"))
    hidden = hidden or "display: none" in (el.get("style") or "")
    if not hidden:
        p = _points(el)
        if p is not None:
            out.append((m @ np.c_[p, np.ones(len(p))].T).T[:, :2])
    for ch in el:
        _collect(ch, m, out, hidden)


def _texts(el) -> list[str]:
    return [t.text.strip() for t in el.iter(NS + "text") if t.text and t.text.strip()]


def parse(svg: Path) -> dict:
    root = ET.parse(svg).getroot()
    objs, floors = [], 0

    def walk(el, parent_m, floor):
        nonlocal floors
        m = parent_m @ _mat(el.get("transform"))
        cls = (el.get("class") or "").strip()
        if cls.startswith("Floorplan"):
            floors += 1
            floor = floors
        if cls.startswith(TOP_PREFIXES):
            pts = []
            _collect(el, parent_m, pts)  # _collect applies el's own transform itself
            if pts:
                p = np.vstack(pts)
                # space polygons: use only the boundary polygon (labels/dimensions are hidden or outside)
                objs.append({"cls": cls, "floor": floor,
                             "bbox": [float(p[:, 0].min()), float(p[:, 1].min()), float(p[:, 0].max()), float(p[:, 1].max())],
                             "names": _texts(el) if cls.startswith("Space") else []})
            if not cls.startswith("Wall"):
                return  # do not descend into a typed object (walls contain their doors/windows)
        for ch in el:
            walk(ch, m, floor)

    walk(root, np.eye(3), 0)
    return {"floors": floors, "objects": objs}


def main():
    out = {}
    for split in ("train", "val", "test"):
        for line in open(SRC / f"{split}.txt"):
            d = line.strip().strip("/")
            if not d:
                continue
            key = d.replace("/", "-")  # high_quality_architectural/1191 -> benchmark file stem
            try:
                out[key] = {"split": split, **parse(SRC / d / "model.svg")}
            except Exception as ex:
                out[key] = {"split": split, "error": str(ex)}
    dst = Path(__file__).resolve().parent.parent / "data_cache" / "cubicasa_annotations.json"
    dst.write_text(json.dumps(out))
    print(len(out), "plans ->", dst, file=sys.stderr)


if __name__ == "__main__":
    main()
