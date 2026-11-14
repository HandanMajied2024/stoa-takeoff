"""Extractor for layered CAD floor plans (Swiss Dwellings DXF: WALL / DOOR / WINDOW / ROOM_OUTLINE /
ROOM_TEXT / FIXTURE / UNIT_OUTLINE layers).

Everything is measured from geometry: room areas are polygon areas in metres, fixtures are
classified from their drawn symbol (outer outline + nested bowl / drain / burner shapes).
"""

from __future__ import annotations

import re
from pathlib import Path

import ezdxf
from shapely.geometry import Point, Polygon

from ..model import Building, Element, Source

ROOM_NUMBER = re.compile(r"^[A-Z]?\d+(\.\d+)?$")
WRITTEN_AREA = re.compile(r"\s*(\d+(?:[.,]\d+)?)\s*m(?:²|2)\s*$")
UNIT_LABEL = re.compile(r"^(Whg\.|Appt\.|App\.|Wohnung|Appartement|Appartamento)\s*([A-Z])$")
OUTDOOR = {"balkon", "balcon", "balcone", "loggia", "terrasse", "terrazza", "terrasse couverte", "sitzplatz", "gartensitzplatz"}
NOT_NET_AREA = {"schacht", "gaine", "cavedio", "luftraum", "vide", "vuoto"}


def _poly(e) -> Polygon | None:
    pts = list(e.get_points("xy"))
    if len(pts) < 3:
        return None
    p = Polygon(pts)
    if not p.is_valid:
        p = p.buffer(0)
    return p if p.area > 1e-6 else None


def classify_fixture(children: list[tuple[str, float | int]], dims: tuple[float, float]) -> str:
    """Classify a fixture symbol from what is drawn inside its outline.

    children: ("poly", n_vertices) or ("circ", radius) for every shape nested in the outline.
    """
    circles = sorted(r for k, r in children if k == "circ")
    polys = sorted(n for k, n in children if k == "poly")
    burners = [r for r in circles if r >= 0.07]
    drains = [r for r in circles if r < 0.07]
    if len(burners) >= 2:
        return "kitchen"
    if 69 in polys or any(n > 60 for n in polys):
        return "bathtub"
    if drains and polys and max(polys) >= 20:
        return "washbasin"          # basin bowl (ellipse) with a drain
    if drains:
        return "shower"             # flat tray with a drain
    if polys and not drains:
        return "wc"
    return "unknown"


def extract(path: str | Path) -> Building:
    path = Path(path)
    msp = ezdxf.readfile(path).modelspace()
    src = str(path)
    b = Building(id=path.stem, source_file=src, source_type="swiss_dxf", levels=["floor"])

    # ---- title / annotations
    for t in msp.query('TEXT[layer=="ANNOTATION"]'):
        if not b.title:
            b.title = t.dxf.text

    # ---- units (apartments)
    units: list[tuple[str, Polygon, str]] = []
    unit_polys = [(e.dxf.handle, _poly(e)) for e in msp.query('LWPOLYLINE[layer=="UNIT_OUTLINE"]')]
    unit_polys = [(h, p) for h, p in unit_polys if p is not None]

    texts = [(t.dxf.text.strip(), Point(t.dxf.insert[0], t.dxf.insert[1])) for t in msp.query('TEXT[layer=="ROOM_TEXT"]')]
    for txt, pt in texts:
        m = UNIT_LABEL.match(txt)
        if not m:
            continue
        hits = [(h, p) for h, p in unit_polys if p.contains(pt)]
        if hits:
            h, p = min(hits, key=lambda hp: hp[1].area)
            units.append((m.group(2), p, h))
    for letter, p, h in units:
        b.elements.append(Element(
            id=f"unit-{letter}", kind="unit", name=letter, polygon=list(p.exterior.coords), area_m2=p.area,
            source=Source(file=src, ref=h, layer="UNIT_OUTLINE", method="dxf.polygon"),
        ))

    # ---- rooms: outline polygon + the label/number texts placed inside it
    rooms = []
    for e in msp.query('LWPOLYLINE[layer=="ROOM_OUTLINE"]'):
        p = _poly(e)
        if p is not None:
            rooms.append({"h": e.dxf.handle, "p": p, "names": [], "nums": [], "written": None})
    for txt, pt in texts:
        if UNIT_LABEL.match(txt):
            continue
        hits = [r for r in rooms if r["p"].contains(pt)]
        if not hits:
            continue
        r = min(hits, key=lambda r: r["p"].area)
        if m := WRITTEN_AREA.search(txt):
            r["written"] = float(m.group(1).replace(",", "."))
            txt = txt[: m.start()].strip()
            if not txt:
                continue
        (r["nums"] if ROOM_NUMBER.match(txt) else r["names"]).append(txt)

    # unlabelled outlines nested inside a labelled room are shafts / voids: not net floor area
    for r in rooms:
        r["voids"] = []
    labelled = [r for r in rooms if r["names"] or r["nums"]]
    for r in rooms:
        if r["names"] or r["nums"]:
            continue
        host = next((h for h in labelled if h["p"].buffer(0.01).contains(r["p"])), None)
        if host:
            host["voids"].append(r["p"])
            r["void_of"] = host

    for i, r in enumerate(rooms):
        if r.get("void_of"):
            b.elements.append(Element(
                id=f"void-{r['h']}", kind="other", subtype="shaft_or_void",
                polygon=list(r["p"].exterior.coords), area_m2=r["p"].area,
                source=Source(file=src, ref=r["h"], layer="ROOM_OUTLINE", method="dxf.polygon"),
            ))
            continue
        name = " ".join(r["names"]) or None
        number = r["nums"][0] if r["nums"] else None
        flags = []
        if not name:
            flags.append("room has no label")
        if r["written"] is not None and abs(r["written"] - r["p"].area) > max(0.05, 0.02 * r["written"]):
            flags.append(f"written area {r['written']:.2f} m² differs from measured {r['p'].area:.2f} m²")
        if len(r["nums"]) > 1:
            flags.append(f"several room numbers inside one outline: {r['nums']}")
        unit = None
        c = r["p"].representative_point()
        for letter, up, _ in units:
            if up.contains(c):
                unit = letter
        low = (name or "").lower()
        b.elements.append(Element(
            id=f"room-{number or i}", kind="room", name=name, number=number, unit=unit,
            polygon=list(r["p"].exterior.coords), area_m2=r["p"].area - sum(v.area for v in r["voids"]), written_area_m2=r["written"],
            outdoor=low in OUTDOOR, confidence=1.0 if name and number else 0.6, flags=flags,
            source=Source(file=src, ref=r["h"], layer="ROOM_OUTLINE", method="dxf.polygon"),
        ))

    # ---- windows: one closed frame per window
    for e in msp.query('LWPOLYLINE[layer=="WINDOW"]'):
        if e.closed or len(e) >= 4:
            p = _poly(e)
            b.elements.append(Element(
                id=f"window-{e.dxf.handle}", kind="window",
                polygon=list(p.exterior.coords) if p else None,
                length_m=max(p.bounds[2] - p.bounds[0], p.bounds[3] - p.bounds[1]) if p else None,
                source=Source(file=src, ref=e.dxf.handle, layer="WINDOW", method="dxf.window_frame"),
            ))

    # ---- doors: one 5-vertex leaf outline per door (swing arcs double-count double doors)
    for e in msp.query('LWPOLYLINE[layer=="DOOR"]'):
        if len(e) == 5:
            p = _poly(e)
            b.elements.append(Element(
                id=f"door-{e.dxf.handle}", kind="door",
                polygon=list(p.exterior.coords) if p else None,
                source=Source(file=src, ref=e.dxf.handle, layer="DOOR", method="dxf.door_leaf"),
            ))

    # ---- fixtures: group nested shapes under their outer outline, classify the symbol
    shapes = []
    for e in msp.query('LWPOLYLINE[layer=="FIXTURE"]'):
        p = _poly(e)
        if p is not None:
            shapes.append(("poly", len(e), p, e.dxf.handle))
    for e in msp.query('CIRCLE[layer=="FIXTURE"]'):
        c = e.dxf.center
        shapes.append(("circ", round(e.dxf.radius, 3), Point(c[0], c[1]).buffer(e.dxf.radius, 8), e.dxf.handle))
    shapes.sort(key=lambda s: -s[2].area)
    tops: list[tuple[tuple, list]] = []
    for s in shapes:
        parent = next((t for t in tops if t[0][2].buffer(0.01).contains(s[2])), None)
        if parent:
            parent[1].append(s)
        else:
            tops.append((s, []))
    for (k, n, g, h), children in tops:
        if k != "poly":
            continue
        x0, y0, x1, y1 = g.bounds
        dims = tuple(sorted((x1 - x0, y1 - y0)))
        ftype = classify_fixture([(c[0], c[1]) for c in children], dims)
        if ftype == "unknown" and not children:
            continue  # plain rectangles: cupboards / counters, not sanitary fixtures
        b.elements.append(Element(
            id=f"fixture-{h}", kind="fixture", subtype=ftype, polygon=list(g.exterior.coords),
            confidence=0.5 if ftype == "unknown" else 1.0,
            flags=["fixture symbol not recognised"] if ftype == "unknown" else [],
            source=Source(file=src, ref=h, layer="FIXTURE", method="dxf.symbol"),
        ))

    b.meta["units"] = sorted(u[0] for u in units)
    return b
