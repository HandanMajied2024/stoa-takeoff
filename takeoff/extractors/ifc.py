"""IFC extractor: quantities are computed from the element geometry, not read from property sets.

Stored quantity sets in real-world models are often stale or computed with different rules
(we measured 17.94 m² stored vs 15.59 m² actual for one room), so geometry is the truth and the
stored value is only used as a cross-check that raises a flag when it disagrees.
"""

from __future__ import annotations

from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as uel
import ifcopenshell.util.unit as uunit
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from ..model import Building, Element, Source

KIND = {
    "IfcSpace": "room", "IfcDoor": "door", "IfcWindow": "window",
    "IfcWall": "wall", "IfcWallStandardCase": "wall", "IfcColumn": "column", "IfcBeam": "beam",
    "IfcStair": "stair", "IfcSlab": "slab",
    "IfcSanitaryTerminal": "fixture", "IfcFlowTerminal": "fixture", "IfcLightFixture": "fixture",
}


def _settings():
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", False)
    return s


def _mesh(settings, el):
    shape = ifcopenshell.geom.create_shape(settings, el)
    g = shape.geometry
    v = np.array(g.verts).reshape(-1, 3)
    f = np.array(g.faces).reshape(-1, 3)
    m = np.array(shape.transformation.matrix).reshape(4, 4).T  # column-major -> 4x4
    return v, f, m


def _volume(v, f) -> float:
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    return float(abs(np.einsum("ij,ij->i", a, np.cross(b, c)).sum()) / 6.0)


def _footprint(v, f, m=None) -> Polygon | None:
    """Union of the downward-facing bottom faces, projected to plan."""
    zmin = v[:, 2].min()
    tris = []
    for t in f:
        p = v[t]
        if np.all(np.abs(p[:, 2] - zmin) < 1e-3):
            if m is not None:
                p = (m @ np.c_[p, np.ones(3)].T).T[:, :3]
            poly = Polygon(p[:, :2])
            if poly.area > 1e-9:
                tris.append(poly)
    if not tris:
        return None
    u = unary_union(tris)
    return u


def _side_area(v, f) -> float:
    """Area of the largest vertical face direction (one side of a wall), in local coordinates."""
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    n = np.cross(b - a, c - a)
    area = np.linalg.norm(n, axis=1) / 2
    nn = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    vertical = np.abs(nn[:, 2]) < 1e-3
    # one side = faces pointing to +y in wall-local axes (length along x)
    side = vertical & (nn[:, 1] > 0.5)
    return float(area[side].sum())


def storey_of(el) -> str | None:
    c = uel.get_container(el)
    while c is not None and not c.is_a("IfcBuildingStorey"):
        c = getattr(c, "Decomposes", None) and c.Decomposes[0].RelatingObject or None
    if c is None:
        # spaces hang below storeys via aggregation
        agg = uel.get_aggregate(el)
        while agg is not None and not agg.is_a("IfcBuildingStorey"):
            agg = uel.get_aggregate(agg)
        c = agg
    return c.Name if c is not None else None


def _stored(el, key: str) -> float | None:
    for pset in uel.get_psets(el, qtos_only=True).values():
        for k, v in pset.items():
            if k == key and isinstance(v, (int, float)):
                return float(v)
    return None


SCALE = {"LENGTHUNIT": 1.0, "AREAUNIT": 1.0, "VOLUMEUNIT": 1.0}
QTO_UNIT = {"Length": "LENGTHUNIT", "Width": "LENGTHUNIT", "Height": "LENGTHUNIT", "Depth": "LENGTHUNIT",
            "Perimeter": "LENGTHUNIT", "NetVolume": "VOLUMEUNIT", "GrossVolume": "VOLUMEUNIT"}


def _qto(el) -> dict:
    """Base quantities converted to SI (models store them in project units: mm, ft, ...)."""
    q: dict = {}
    for name, pset in uel.get_psets(el, qtos_only=True).items():
        if "BaseQuantities" in name:
            for k, v in pset.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    unit = QTO_UNIT.get(k, "AREAUNIT" if "Area" in k else None)
                    q[k] = v * SCALE[unit] if unit else v
    return q


def _parts(el) -> list:
    return [p for p in (uel.get_decomposition(el) or []) if p.is_a("IfcBuildingElementPart")]


def _geom_metrics(st, el) -> dict:
    """Geometry of an element, or of its layer parts when the element itself has no body."""
    try:
        v, fc, m = _mesh(st, el)
        return {"volume": _volume(v, fc), "length": float(v[:, 0].max() - v[:, 0].min()),
                "side": _side_area(v, fc), "mesh": (v, fc, m)}
    except Exception:
        parts = _parts(el)
        if not parts:
            raise
        ms = [_geom_metrics(st, p) for p in parts]
        return {"volume": sum(x["volume"] for x in ms), "length": max(x["length"] for x in ms),
                "side": max(x["side"] for x in ms), "mesh": None, "from_parts": len(parts)}


def _agree(e: Element, label: str, official: float | None, computed: float | None):
    if official and computed and abs(official - computed) > 0.02 * abs(official):
        e.flags.append(f"{label}: base quantity {official:.2f} vs geometry {computed:.2f}")


def _measure(st, el, e: Element, kind: str):
    """Official IFC base quantities first (what estimators exchange), geometry as fallback + cross-check.
    Rooms always use geometry: space quantity sets are frequently stale in real models."""
    q = _qto(el)
    try:
        g = _geom_metrics(st, el)
    except Exception as ex:
        g = None
        e.flags.append(f"geometry failed: {type(ex).__name__}")
    if kind == "room":
        if g and g["mesh"]:
            v, fc, m = g["mesh"]
            fp = _footprint(v, fc)
            e.area_m2 = fp.area if fp is not None else None
            wfp = _footprint(v, fc, m)
            if wfp is not None and wfp.geom_type == "Polygon":
                e.polygon = [tuple(map(float, c)) for c in wfp.exterior.coords]
        e.source.method = "ifc.geometry"
        return
    gv = g["volume"] if g else None
    e.volume_m3 = q.get("NetVolume") or gv
    _agree(e, "volume", q.get("NetVolume"), gv)
    if kind == "wall":
        gl = g["length"] if g else None
        e.length_m = q.get("Length") or gl
        e.side_area_m2 = q.get("NetSideArea") or (g["side"] if g else None)
    e.source.method = "ifc.base_quantities" if q else ("ifc.geometry.parts" if g and g.get("from_parts") else "ifc.geometry")
    if e.volume_m3 is None:
        e.confidence = 0.5


def extract(path: str | Path) -> Building:
    path = Path(path)
    f = ifcopenshell.open(str(path))
    st = _settings()
    for u in SCALE:
        try:
            SCALE[u] = uunit.calculate_unit_scale(f, u)
        except Exception:
            SCALE[u] = 1.0
    proj = f.by_type("IfcProject")
    site = f.by_type("IfcBuilding")
    b = Building(id=path.stem, source_file=str(path), source_type="ifc",
                 title=(site[0].Name if site else None) or (proj[0].Name if proj else None))
    b.meta["project_name"] = proj[0].Name if proj else None
    b.meta["project_long_name"] = proj[0].LongName if proj else None
    b.meta["building_names"] = [x.Name for x in site]
    b.levels = [s.Name for s in f.by_type("IfcBuildingStorey")]

    seen = set()
    for cls, kind in KIND.items():
        try:
            items = f.by_type(cls, include_subtypes=False)
        except RuntimeError:  # class not in this schema (IFC2X3 vs IFC4)
            continue
        for el in items:
            if el.id() in seen:
                continue
            seen.add(el.id())
            parent = uel.get_aggregate(el)
            if parent is not None and parent.is_a() == el.is_a():
                continue  # a riser/tread modelled as IfcStair inside an IfcStair is a component, not a stair
            subtype = el.is_a()
            if kind == "fixture":
                subtype = "light" if el.is_a("IfcLightFixture") else "sanitary"
                if el.is_a("IfcFlowTerminal"):
                    t = uel.get_type(el)
                    tname = (t.is_a() if t else "")
                    subtype = "light" if "Light" in tname else "sanitary" if "Sanitary" in tname else "flow_terminal"
            e = Element(
                id=el.GlobalId, kind=kind, subtype=subtype,
                name=getattr(el, "LongName", None) if kind == "room" else el.Name,
                number=el.Name if kind == "room" else None,
                level=storey_of(el),
                source=Source(file=str(path), ref=el.GlobalId, method="ifc.geometry"),
            )
            if kind in {"room", "wall", "slab", "column", "beam"} and (el.Representation or _parts(el)):
                _measure(st, el, e, kind)
            if kind == "room" and e.area_m2:
                stored = _stored(el, "NetFloorArea")
                if stored and abs(stored - e.area_m2) > 0.02 * e.area_m2:
                    e.flags.append(f"stored NetFloorArea {stored:.2f} m² differs from geometry {e.area_m2:.2f} m²")
            b.elements.append(e)
    return b
