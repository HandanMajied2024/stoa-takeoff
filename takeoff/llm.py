"""Chat question -> structured Query.

Claude only *interprets* the question: it fills the same Query object the benchmark parser fills,
using the vocabulary actually present in this building (room labels, apartments, levels). The
deterministic engine then does every count and sum, so the number never comes from the LLM.
Without an API key the keyword parser is used instead.
"""

from __future__ import annotations

import collections
import re
import os

from pydantic import BaseModel

from . import questions
from .model import Building
from .questions import Query

MODEL = "claude-opus-5-5"


class Interpretation(BaseModel):
    understood: bool
    query: Query | None = None
    clarification: str | None = None   # what to ask the user when the question is ambiguous
    note: str | None = None            # how the question was read, in one short sentence


SYSTEM = """You translate a construction professional's question about ONE building drawing into a
structured Query for a deterministic takeoff engine. You never compute numbers yourself.

Query fields:
- op: "count" | "area" (m2, sums area_m2) | "length" (m) | "volume" (m3) | "side_area" (wall face m2)
      | "perimeter" (room outline length, m) | "wall_area" (room perimeter x height: tiles, paint,
      waterproofing on walls).
- kind: one of the element kinds listed in the building vocabulary (room, door, window, fixture, unit,
  wall, slab, ...).
- subtype: for fixtures: wc, washbasin, sink, bathtub, shower, kitchen, sauna_stove ... ; use the group
  "sink_any" for any basin/sink and "bath_or_shower" for showers + bathtubs together. For rooms from
  scanned plans the subtype is the room type (bedroom, kitchen, bathroom, wc, balcony, sauna). On vector
  plans use subtype "wet" for bathrooms/WCs/wet rooms: rooms that contain a WC, bathtub, shower or basin.
- room_names: list of room labels EXACTLY as they appear in the vocabulary, e.g. every label that means a
  bathroom ("Bad", "Salle de bain", "Bagno", "KPH", "WC") when asked about bathrooms or toilets as rooms.
- room_number / unit (apartment letter) / level (exact level name) with scope "level" to filter.
- indoor_only: exclude balconies/terraces. exclude_shared: exclude stairwells/lifts.
- height_m: only if the user states a wall height.

Rules: "toilets" usually means WC fixtures (kind fixture, subtype wc). Material for a room's floor ->
op area; for its walls -> op wall_area. If the question cannot be expressed with these fields, or names
something not in the vocabulary, set understood=false and write a short clarification question.
Write `note` as one short sentence saying how you read the question."""


def vocabulary(b: Building) -> str:
    kinds = collections.Counter((e.kind, e.subtype) for e in b.elements)
    rooms = collections.Counter((e.name or "").strip() for e in b.elements if e.kind == "room" and e.name)
    units = sorted({e.unit for e in b.elements if e.unit})
    lines = [f"source type: {b.source_type}", f"levels: {b.levels}",
             "elements (kind/subtype: count): " + ", ".join(f"{k}/{s or '-'}: {n}" for (k, s), n in kinds.most_common()),
             "room labels: " + ", ".join(f"{r} ({n})" for r, n in rooms.most_common(150))]
    if units:
        lines.append(f"apartments: {units}")
    return "\n".join(lines)


CASUAL = [  # last-resort chat keywords (no API key): (words, kind, subtype)
    (("sauna stove", "kiuas", "kiukaa"), "fixture", "sauna_stove"),
    (("toilet", "wc", "vessa", "wc-istuin"), "fixture", "wc"),
    (("sink", "basin", "lavuaari", "pesuallas", "pesualtaa"), "fixture", "sink_any"),
    (("shower", "suihku"), "fixture", "shower"),
    (("bathtub", "amme"), "fixture", "bathtub"),
    (("bedroom", "makuuhuone"), "room", "bedroom"),
    (("kitchen", "keittio", "keittiö"), "room", "kitchen"),
    (("balcon", "parvek"), "room", "balcony"),
    (("door", "ovi", "ovea", "ovet"), "door", None),
    (("window", "ikkun"), "window", None),
    (("apartment", "asunto", "asunno"), "unit", None),
    (("room", "huone"), "room", None),
]


# room type -> how that room is labelled on vector plans (German/French/Italian/English/Finnish)
ROOM_LABELS = {
    "bathroom": re.compile(r"\b(bad|dusche|wc|douche|salle de bains?|bagno|doccia|bath|toilet|kph|ph|pesuh)", re.I),
    "bedroom": re.compile(r"\b(zimmer|schlafen|chambre|camera|bedroom|mh)\b", re.I),
    "kitchen": re.compile(r"\b(k(ü|u)che|cuisine|cucina|kitchen|k|kk|keitti)", re.I),
}
WET_WORDS = ("bathroom", "bath room", "wet room", "kylpyhuone", "kph", "toilet room", "märkä", "marka", "pesuhuone")


def _keyword(question: str, b: Building | None = None) -> Query | None:
    t = question.lower()
    op = "wall_area" if "wall" in t and any(w in t for w in ("tile", "paint", "area", "plaster", "waterproof")) else \
        "area" if any(w in t for w in ("area", "m2", "m²", "pinta-ala", "floor tile", "flooring")) else "count"
    room_type = "bathroom" if any(w in t for w in WET_WORDS) or (op == "wall_area" and "toilet" in t) else \
        "bedroom" if "bedroom" in t or "makuuhuone" in t else "kitchen" if op != "count" and "kitchen" in t else None
    if room_type and b is not None:
        if b.source_type == "raster":
            return Query(op=op, kind="room", subtype=room_type)
        if room_type == "bathroom":  # labels are often missing: use the fixtures inside the room
            return Query(op=op, kind="room", subtype="wet")
        labels = sorted({e.name for e in b.elements if e.kind == "room" and e.name and ROOM_LABELS[room_type].search(e.name)})
        if labels:
            return Query(op=op, kind="room", room_names=labels)
    q = questions.parse(question)
    if q is None:  # the benchmark templates say "on this floor plan"; casual chat often does not
        q = questions.parse(question.rstrip("?. ") + " in this floor plan?")
    if q is None:
        for words, kind, sub in CASUAL:
            if any(w in t for w in words):
                return Query(op=op if kind in ("room", "unit") else "count", kind=kind, subtype=sub)
    return q


def interpret(b: Building, question: str, history: list[dict] | None = None) -> tuple[Interpretation, str]:
    """Returns (interpretation, interpreter name)."""
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        q = _keyword(question, b)
        return (Interpretation(understood=q is not None, query=q,
                               clarification=None if q else "I could not map that to a takeoff query. Try e.g. "
                               "'How many doors?' or 'Total area of the bathrooms'.")), "keyword parser"
    import anthropic

    client = anthropic.Anthropic()
    msgs = [{"role": m["role"], "content": m["content"]} for m in (history or [])[-6:]]
    msgs.append({"role": "user", "content": f"Building vocabulary:\n{vocabulary(b)}\n\nQuestion: {question}"})
    try:
        r = client.messages.parse(model=MODEL, max_tokens=4000, system=SYSTEM, messages=msgs,
                                  output_config={"effort": "low"}, output_format=Interpretation)
    except anthropic.APIError as ex:
        q = _keyword(question, b)
        return Interpretation(understood=q is not None, query=q,
                              note=f"Claude unavailable ({type(ex).__name__}); keyword parser used"), "keyword parser"
    if r.stop_reason == "refusal" or r.parsed_output is None:
        q = _keyword(question, b)
        return Interpretation(understood=q is not None, query=q), "keyword parser"
    return r.parsed_output, MODEL
