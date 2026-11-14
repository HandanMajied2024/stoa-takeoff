"""Finnish (and Swedish) room abbreviations on residential floor plans -> room types.

Each OCR token is normalised (case, OCR digit/letter confusions, trailing numbers like "MH2") and
matched against an abbreviation table. Compound labels ("3H+TUPAK.+S") describe the whole
apartment and are ignored for room counting.
"""

from __future__ import annotations

import re

# room type -> abbreviations as they appear on Finnish plans
ROOM_ABBR: dict[str, set[str]] = {
    "bedroom": {"MH", "MAKUUH", "MAKUUHUONE", "SOV", "SOVRUM"},
    "bathroom": {"KH", "KPH", "PH", "PESUH", "PESUHUONE", "KYLPYH", "KYLPYHUONE", "SH", "SUIHKU", "TH",
                 "BADRUM", "TVÄTTRUM", "PESUTILA"},
    "wc": {"WC"},
    "sauna": {"S", "SAUNA", "LH", "LÖYLYH", "BASTU"},
    "kitchen": {"K", "KK", "KEITTIÖ", "KEITTIO", "TK", "TUPAK", "TUPAKEITTIÖ", "AVOK", "KT", "KEITTOKOMERO",
                "APUK", "KÖK", "KOK", "KEITTOTILA", "AVOKEITTIÖ"},
    "balcony": {"PARVEKE", "PARV", "LASITETTU PARVEKE", "LASIT. PARVEKE", "BALKONG", "RANSKALAINEN PARVEKE"},
    "living": {"OH", "OLOH", "OLOHUONE", "TUPA", "AH", "VARDAGSRUM"},
    "room": {"H", "HUONE", "AH"},
    "utility": {"KHH", "KODINHOITOH", "VAR", "VH", "ET", "TEKN", "TK"},
}

OCR_FIX = str.maketrans({"0": "O", "1": "I", "5": "S", "|": "I", "€": "E"})
SPLIT = re.compile(r"[+/,]")
FLOOR = re.compile(r"(\d)\s*\.?\s*(krs|kerros|kerr|kr|vån|plan)\b|\b(kellari|ullakko|pohjakerros|vintti|källare|kellarikerros)\b", re.I)


def normalise(tok: str) -> str:
    t = tok.strip().upper().replace(" ", "")
    t = re.sub(r"\d+([.,]\d+)?M2$", "", t)        # "KH 4.5m2" -> "KH"
    t = re.sub(r"\d+$", "", t)                      # "MH2" -> "MH"
    t = t.rstrip(".:;-")
    if t and not t.isalpha():
        t = t.translate(OCR_FIX)
    return t


def room_types(token: str) -> list[str]:
    """Room types named by a single OCR token. Compound apartment descriptors ("3H+K+S") -> []."""
    if len(SPLIT.split(token)) > 1 and re.match(r"^\d", token.strip()):
        return []
    t = normalise(token)
    out = [rt for rt, abbr in ROOM_ABBR.items() if t in abbr]
    return out


def floor_labels(tokens: list[str]) -> set[str]:
    found = set()
    for tok in tokens:
        for m in FLOOR.finditer(tok):
            found.add((m.group(1) or "") + (m.group(3) or "").lower())
    return found
