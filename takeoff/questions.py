"""Turn a natural-language takeoff question into a structured Query.

The benchmark questions come from fixed templates in ~10 languages, so a keyword parser is exact
and free. In the product, the chat LLM fills the same Query object via tool calling, and the same
deterministic engine answers it - the LLM never does the arithmetic.
"""

from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel

QUOTED = re.compile(r"'(.+?)'(?=[\s),?]|$)|„([^“”]+)[“”]|«\s?([^»]+?)\s?»")


class Query(BaseModel):
    op: str                       # count | area | volume | length | side_area
    kind: str | None = None       # room | door | window | fixture | unit | wall | ...
    subtype: str | None = None    # wc | washbasin | bathtub | shower | sanitary | light
    room_name: str | None = None
    room_number: str | None = None
    room_label: str | None = None  # IFC "Name (Number)" label
    unit: str | None = None
    level: str | None = None
    scope: str = "drawing"        # drawing | model | level
    indoor_only: bool = False
    numbered_only: bool = False
    exclude_shared: bool = False  # stairwells / lifts are not part of an apartment
    single: bool = False          # area of one named element (vs total)
    room_names: list[str] | None = None  # any of these room labels (chat: "all bathrooms")
    height_m: float | None = None  # wall height for wall_area; None -> default, flagged as an assumption


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


# keyword -> (kind, subtype). Order matters: specific before generic.
TERMS: list[tuple[tuple[str, ...], str, str | None]] = [
    (("sanitary fixture", "sanitar", "sanitaire", "sanitari"), "fixture", "sanitary"),
    (("light fixture", "iluminat", "leuchte", "verlichting"), "fixture", "light"),
    (("washbasin", "lavabo", "lavabi"), "fixture", "washbasin"),
    (("bathtub", "badewanne", "baignoire", "vasche da bagno", "vasca"), "fixture", "bathtub"),
    (("shower", "dusche", "douche", "docce", "doccia"), "fixture", "shower"),
    (("toilets (wc)", "wcs", "combien de wc", "quanti wc"), "fixture", "wc"),
    (("apartment", "wohnung", "appartement", "appartament", "logement", "unita abitativ"), "unit", None),
    (("door", "tur", "porte", "porta", "puerta", "deur", "dor", "døre", "dør", "drzwi", " ust "), "door", None),
    (("window", "fenster", "fenetre", "finestr", "ventana", "raam", "ramen", "vindu", "akent", "okien", "ferestre"), "window", None),
    (("slab", "decken", "vloeren", "plader", "dæk", "plyt", "solai", "losas"), "slab", None),
    (("wall", "wande", "wanden", "vaegge", "vægge", "vaeg", "seina", "muri", "muros", "pereti", "scian", "murs"), "wall", None),
    (("column", "stutze", "kolommen", "søjler", "soejler", "sojler", "posti", "pilares", "stalpi", "slup", "pilastri"), "column", None),
    (("beam", "trager", "balken", "bjælker", "tala ", "vigas", "grinzi", "belek", "travi"), "beam", None),
    (("stair", "treppe", "trap", "treppi", "escalera", "scari", "schod", "scale"), "stair", None),
    (("room", "space", "raum", "raume", "ruimte", "rum", "ruumi", "local", "pomieszcze", "piece", "pièce", "stanz"), "room", None),
]

COUNT_WORDS = ("how many", "kuinka monta", "wie viele", "combien", "quant", "hoeveel", "hvor mange", "mitu", "ile ",
               "numero de", "numero di", "numarul", "numărul", "el numero")
VOLUME_WORDS = ("m³", "m3", "volume", "volumen", "volum")
LENGTH_WORDS = ("length", "lang sind", "lengte", "laengde", "længde", "pikkus", "dlugosc", "longitud", "lunghezza")
SIDE_WORDS = ("side area", "seitenflache", "seiten", "zijoppervlakte", "sideareal", "kulgpinna")
MODEL_WORDS = ("model", "modellen", "mudelis", "modell", "modelu", "modello", "modelo", "mudel", "modelul")
APT_LETTER = re.compile(r"(?:apartment|wohnung|appartement|appartamento|l'appartement|dell'appartamento)\s+([A-Z])\b", re.I)
ROOM_NUM = re.compile(r"\b(?:room|raum|pi[eè]ce|locale)\s+([A-Z]?\d+(?:\.\d+)?)\s*\(", re.I)


def _kind(qn: str) -> tuple[str | None, str | None]:
    padded = f" {qn} "
    for words, kind, sub in TERMS:
        if any(w in padded for w in words):
            return kind, sub
    return None, None


# Finnish residential plan questions (CubiCasa): checked first, most specific first.
PLAN_COUNTS: list[tuple[tuple[str, ...], str, str | None]] = [
    (("bathrooms or washrooms", "kylpy- tai pesuhuone"), "room", "bathroom"),
    (("separate wc room", "erillista wc-tilaa"), "room", "wc"),
    (("toilet bowl", "wc seat", "wc-istuin"), "fixture", "wc"),
    (("sinks and wash basins", "pesu- ja tiskiallas"), "fixture", "sink_any"),
    (("showers and bathtubs", "suihkua ja kylpyammetta"), "fixture", "bath_or_shower"),
    (("floors (storeys)", "kerrosta"), "floor", None),
    (("sauna",), "room", "sauna"),
    (("kitchens", "keittio"), "room", "kitchen"),
    (("bedroom", "makuuhuone"), "room", "bedroom"),
    (("balcon", "parveke"), "room", "balcony"),
    (("how many doors are shown", "kuinka monta ovea"), "door", None),
    (("how many windows are shown", "kuinka monta ikkunaa"), "window", None),
]


def parse(question: str) -> Query | None:
    quoted = [next(g for g in m.groups() if g) for m in QUOTED.finditer(question)]
    # keywords must come from the question itself, never from a quoted model / level / room name
    qn = _norm(QUOTED.sub(" X ", question))
    is_count = any(w in qn for w in COUNT_WORDS) and "m²" not in question
    if is_count and ("floor plan" in qn or "pohjapiirus" in qn) and not quoted:
        for words, kind, sub in PLAN_COUNTS:
            if any(w in qn for w in words):
                return Query(op="count", kind=kind, subtype=sub)

    # ---- Swiss-style per-drawing questions (no level / model given)
    if m := ROOM_NUM.search(question):
        return Query(op="area", kind="room", room_number=m.group(1), room_name=quoted[0] if quoted else None, single=True)
    if (m := APT_LETTER.search(question)) and not is_count:
        return Query(op="area", kind="room", unit=m.group(1).upper(), indoor_only=True, numbered_only=True,
                     exclude_shared=True)
    if "numbered" in qn or "nummerierten" in qn or "numerotees" in qn or "numerati" in qn:
        return Query(op="area", kind="room", indoor_only=True, numbered_only=True)
    if any(w in qn for w in ("labelled", "bezeichnung", "designation", "denominazione", "designees", "denominati")):
        return Query(op="count" if is_count else "area", kind="room", room_name=quoted[0] if quoted else None)

    # ---- IFC-style questions: model scope or level scope
    scope = "model" if any(f" {w} " in f" {qn} " for w in MODEL_WORDS) else ("level" if quoted else "drawing")
    level = quoted[-1] if scope == "level" and quoted else None

    if is_count:
        kind, sub = _kind(qn)
        if kind is None:
            return None
        return Query(op="count", kind=kind, subtype=sub, scope=scope, level=level)

    op = "volume" if any(w in qn for w in VOLUME_WORDS) else \
         "side_area" if any(w in qn for w in SIDE_WORDS) else \
         "length" if any(w in qn for w in LENGTH_WORDS) else "area"
    kind, _ = _kind(qn)
    if op == "area" and kind in (None, "room"):
        if len(quoted) >= 2:   # one room on one level
            return Query(op="area", kind="room", room_label=quoted[0], level=quoted[1], scope="level", single=True)
        return Query(op="area", kind="room", level=level, scope=scope)
    return Query(op=op, kind=kind or "wall", level=level, scope=scope)
