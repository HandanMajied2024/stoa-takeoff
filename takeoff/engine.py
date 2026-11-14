"""Deterministic query engine: answers a Query from a Building and records every step,
so the UI can show *exactly* which elements were counted or summed and why."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .model import Building, Element
from .questions import Query

OUTDOOR = {"balkon", "balcon", "balcone", "loggia", "terrasse", "terrazza", "terrace", "balcony", "parveke", "terassi"}
SHARED = {"treppenhaus", "lift", "cage d'escalier", "vano scala", "ascenseur", "ascensore", "stairwell"}
SUBTYPE_GROUPS = {"sink_any": {"washbasin", "sink"}, "bath_or_shower": {"bathtub", "shower"}}
NOT_NET = {"schacht", "gaine", "cavedio", "luftraum", "vide", "vuoto", "shaft", "void"}


class Answer(BaseModel):
    value: float | int | None
    unit: str
    elements: list[str] = Field(default_factory=list)   # ids of the elements used
    steps: list[str] = Field(default_factory=list)      # human-readable reasoning trace
    flags: list[str] = Field(default_factory=list)      # anything a human should double-check
    confidence: float = 1.0


def _label(e: Element) -> str:
    return f"{e.name} ({e.number})" if e.name and e.number else (e.name or e.number or e.id)


def _is_outdoor(e: Element) -> bool:
    n = (e.name or "").lower()
    return e.outdoor or any(w in n for w in OUTDOOR)


def run(b: Building, q: Query) -> Answer:
    els = [e for e in b.elements if e.kind == q.kind]
    wet_note = None
    if q.kind == "room" and q.subtype == "wet" and b.source_type != "raster":
        els, wet_note = _wet_rooms(b, els)
    elif q.subtype:
        want = SUBTYPE_GROUPS.get(q.subtype, {q.subtype})
        els = [e for e in els if e.subtype in want]
    steps = [f"Source: {b.source_type} '{b.source_file.rsplit('/', 1)[-1]}'",
             f"Selected {len(els)} {q.kind}{'/' + q.subtype if q.subtype else ''} elements"]
    if wet_note:
        steps.append(wet_note)

    if q.level and q.scope == "level":
        lv = q.level.strip()
        els = [e for e in els if (e.level or "").strip() == lv]
        steps.append(f"Kept {len(els)} on level '{lv}'")

    if q.room_number:
        els = [e for e in els if e.number == q.room_number]
        steps.append(f"Room number {q.room_number}: {len(els)} match")
    elif q.room_label:
        lab = q.room_label.strip()
        els = [e for e in els if _label(e) == lab or e.name == lab or e.number == lab]
        steps.append(f"Room '{lab}': {len(els)} match")
    elif q.room_name:
        els = [e for e in els if (e.name or "").strip() == q.room_name.strip()]
        steps.append(f"Rooms labelled '{q.room_name}': {len(els)}")
    if q.room_names:
        want = {n.strip().lower() for n in q.room_names}
        els = [e for e in els if (e.name or "").strip().lower() in want or (e.subtype or "").lower() in want]
        steps.append(f"Rooms labelled {', '.join(sorted(want))}: {len(els)}")
    if q.unit:
        els = [e for e in els if e.unit == q.unit]
        steps.append(f"In apartment {q.unit}: {len(els)} {q.kind}{'s' if len(els) != 1 else ''}")
    if q.indoor_only:
        out = [e for e in els if _is_outdoor(e)]
        els = [e for e in els if not _is_outdoor(e) and not any(w in (e.name or "").lower() for w in NOT_NET)]
        if out:
            steps.append(f"Excluded {len(out)} outdoor spaces: " + ", ".join(_label(e) for e in out))
    if q.numbered_only:
        els = [e for e in els if e.number]
    if q.exclude_shared:
        shared = [e for e in els if (e.name or "").strip().lower() in SHARED]
        els = [e for e in els if e not in shared]
        if shared:
            steps.append("Excluded shared circulation: " + ", ".join(_label(e) for e in shared))

    flags = [f"{_label(e)}: {fl}" for e in els for fl in e.flags]
    conf = min([e.confidence for e in els], default=1.0)

    if q.op == "count":
        return Answer(value=len(els), unit="count", elements=[e.id for e in els], steps=steps + [f"Count = {len(els)}"],
                      flags=flags, confidence=conf)

    if q.op in ("perimeter", "wall_area"):
        return _walls(b, q, els, steps, flags, conf)

    attr = {"area": "area_m2", "volume": "volume_m3", "length": "length_m", "side_area": "side_area_m2"}[q.op]
    unit = {"area": "m2", "volume": "m3", "length": "m", "side_area": "m2"}[q.op]
    if q.single and len(els) != 1:
        return Answer(value=None, unit=unit, steps=steps + [f"Expected exactly one element, found {len(els)}"],
                      flags=["ambiguous or missing element"], confidence=0.0)
    vals = [(e, getattr(e, attr)) for e in els]
    missing = [e for e, v in vals if v is None]
    if missing:
        flags.append(f"{len(missing)} elements have no measurable {q.op}")
    total = sum(v for _, v in vals if v is not None)
    for e, v in vals[:40]:
        if v is not None:
            steps.append(f"  {_label(e)}: {v:.2f} {unit}")
    steps.append(f"Total = {total:.2f} {unit}")
    return Answer(value=round(total, 3), unit=unit, elements=[e.id for e, _ in vals], steps=steps, flags=flags,
                  confidence=conf if not missing else min(conf, 0.5))


DEFAULT_HEIGHT_M = 2.6
WET_FIXTURES = {"wc", "bathtub", "shower", "washbasin"}


def _wet_rooms(b: Building, rooms: list[Element]) -> tuple[list[Element], str]:
    """Wet rooms = rooms that contain a WC, bathtub, shower or washbasin (labels are often missing)."""
    from shapely.geometry import Polygon
    fx = [e for e in b.elements if e.kind == "fixture" and e.subtype in WET_FIXTURES and e.polygon]
    out = []
    for r in rooms:
        if not r.polygon or len(r.polygon) < 3:
            continue
        poly = Polygon(r.polygon).buffer(0.05)
        if any(poly.contains(Polygon(f.polygon).representative_point()) for f in fx):
            out.append(r)
    return out, f"Wet room = room containing a WC, bathtub, shower or washbasin: {len(out)} rooms"


def _perimeter(e: Element) -> float | None:
    if not e.polygon or len(e.polygon) < 3:
        return None
    from shapely.geometry import Polygon
    return Polygon(e.polygon).exterior.length


def _walls(b: Building, q: Query, els: list[Element], steps, flags, conf) -> Answer:
    """Room perimeter, and wall-finish area = perimeter x height (tiles, paint, waterproofing)."""
    if b.source_type == "raster":
        return Answer(value=None, unit="m", steps=steps + ["Scanned plan has no verified scale: lengths are in pixels"],
                      flags=["no drawing scale: measure a known dimension first"], confidence=0.0)
    total_p = 0.0
    for e in els:
        p = _perimeter(e)
        if p is None:
            flags.append(f"{_label(e)}: no outline, perimeter unknown")
            continue
        total_p += p
        steps.append(f"  {_label(e)}: perimeter {p:.2f} m")
    steps.append(f"Total perimeter = {total_p:.2f} m")
    if q.op == "perimeter":
        return Answer(value=round(total_p, 2), unit="m", elements=[e.id for e in els], steps=steps, flags=flags,
                      confidence=conf)
    h = q.height_m or DEFAULT_HEIGHT_M
    if not q.height_m:
        flags.append(f"wall height not in the drawing: assumed {h} m (set it to recalculate)")
    area = total_p * h
    steps.append(f"Wall area = {total_p:.2f} m x {h} m = {area:.2f} m2 (door/window openings not subtracted)")
    return Answer(value=round(area, 2), unit="m2", elements=[e.id for e in els], steps=steps, flags=flags,
                  confidence=min(conf, 0.7))
