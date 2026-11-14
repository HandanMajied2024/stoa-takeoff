"""Building model: the single source of truth every extractor writes and every query reads.

Every element keeps a pointer back to where it came from (file, layer/GUID, method), so any
number we answer can be traced to the drawing and highlighted in the viewer.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Kind = Literal[
    "room", "unit", "door", "window", "fixture", "wall", "slab", "column",
    "beam", "stair", "space_label", "floor", "other",
]

# Fixture subtypes we recognise across sources.
FixtureType = Literal[
    "wc", "washbasin", "sink", "bathtub", "shower", "kitchen", "washing_machine",
    "sauna_stove", "urinal", "light", "sanitary_other", "unknown",
]


class Source(BaseModel):
    file: str
    ref: str | None = None          # DXF handle, IFC GUID, SVG id, bbox id...
    layer: str | None = None
    method: str                     # e.g. "dxf.polygon", "ifc.geometry", "yolo", "ocr"


class Element(BaseModel):
    id: str
    kind: Kind
    subtype: str | None = None      # fixture type, IFC class, door type...
    name: str | None = None         # room label as written on the plan ("Bad", "KPH")
    number: str | None = None       # room number ("7.05", "A102")
    unit: str | None = None         # apartment / unit id the element belongs to
    level: str | None = None
    polygon: list[tuple[float, float]] | None = None   # plan outline in metres
    area_m2: float | None = None
    written_area_m2: float | None = None   # area printed on the drawing (cross-check)
    length_m: float | None = None
    volume_m3: float | None = None
    side_area_m2: float | None = None
    outdoor: bool = False
    confidence: float = 1.0
    flags: list[str] = Field(default_factory=list)      # why a human should look
    source: Source
    classified_by: str | None = None   # rule id that (re)classified this element, see takeoff/rules.py
    reviewed: str | None = None        # human decision: "ok", "no" or "label:<label>"


class Building(BaseModel):
    id: str
    source_file: str
    source_type: str                # "swiss_dxf", "ifc", "raster", ...
    title: str | None = None
    levels: list[str] = Field(default_factory=list)
    elements: list[Element] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)

    def of(self, kind: str, subtype: str | None = None, level: str | None = None) -> list[Element]:
        return [
            e for e in self.elements
            if e.kind == kind
            and (subtype is None or e.subtype == subtype)
            and (level is None or e.level == level)
        ]
