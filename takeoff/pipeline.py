"""Route a drawing to the right extractor and cache the resulting Building model as JSON."""

from __future__ import annotations

import re
from pathlib import Path

from .model import Building

CACHE = Path(__file__).resolve().parent.parent / "data_cache" / "buildings"
IFC_VIEW = re.compile(r"_(plan|section|elevation)-.*$")


def resolve(path: str | Path) -> tuple[str, Path] | None:
    """Pick the best machine-readable file for a drawing: vector/BIM beats raster."""
    p = Path(path)
    src = p.parent.name
    if src == "swiss_dwellings":
        dxf = p.with_suffix(".dxf")
        return ("swiss_dxf", dxf) if dxf.exists() else None
    if src == "cubicasa5k" or p.suffix.lower() in (".png", ".jpg", ".jpeg"):
        return "raster", p
    if src in ("ifc_models", "ifc_bench"):
        if p.suffix == ".ifc":
            return "ifc", p
        model = p.parent / (IFC_VIEW.sub("", p.stem) + ".ifc")
        return ("ifc", model) if model.exists() else None
    if p.suffix.lower() == ".dxf":  # uploads: Swiss-style layer conventions
        return "swiss_dxf", p
    if p.suffix.lower() == ".ifc":
        return "ifc", p
    return None


def load(path: str | Path, use_cache: bool = True, review: bool = True) -> Building | None:
    """Extracted building with learned rules and reviewer decisions applied (see takeoff/rules.py)."""
    b = load_raw(path, use_cache)
    if b is None or not review:
        return b
    from . import rules
    return rules.apply(b, drawing=str(path))


def load_raw(path: str | Path, use_cache: bool = True) -> Building | None:
    r = resolve(path)
    if r is None:
        return None
    kind, file = r
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / f"{file.parent.name}__{file.stem}.json"
    if use_cache and cached.exists():
        return Building.model_validate_json(cached.read_text())
    if kind == "raster":
        from .extractors import raster as ex
        return ex.extract(file)  # detections/OCR are cached; thresholds may change, so don't cache the model
    if kind == "swiss_dxf":
        from .extractors import swiss_dxf as ex
    else:
        from .extractors import ifc as ex
    b = ex.extract(file)
    cached.write_text(b.model_dump_json())
    return b
