"""Review learning loop.

A reviewer's decision is stored, and labelling an element teaches a *rule*: the element's
observable signature (source, kind, labelled?, numbered?, fixtures inside, area range) -> a label.
Rules apply to every drawing, are shown with their evidence, and earn trust: each confirmation
raises confidence; once trusted, matches no longer need review; rejections switch a rule off.
Human decisions on a specific element always win over rules.

Everything is deterministic and inspectable: models/learned_rules.json and data_cache/reviews.jsonl.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path

from shapely.geometry import Polygon

from .model import Building, Element

ROOT = Path(__file__).resolve().parent.parent
RULES_FILE = ROOT / "models" / "learned_rules.json"
REVIEWS_FILE = ROOT / "data_cache" / "reviews.jsonl"
WET = {"wc", "bathtub", "shower", "washbasin"}
TRUSTED = 0.9
MIN_DRAWINGS = 3   # a rule is trusted only after confirmations on this many different drawings
_lock = threading.Lock()

# label -> what the element becomes
LABELS = {
    "shaft": {"kind": "other", "subtype": "shaft", "text": "Shaft / duct"},
    "bathroom": {"kind": "room", "subtype": "bathroom", "text": "Bathroom"},
    "storage": {"kind": "room", "subtype": "storage", "text": "Storage / closet"},
    "corridor": {"kind": "room", "subtype": "corridor", "text": "Corridor"},
    "not_a_room": {"kind": "other", "subtype": "not_a_room", "text": "Not a room"},
}

SEED = [  # starting knowledge from analysing the Swiss plans; reviewers confirm or overrule it
    {"id": "seed-shaft", "label": "shaft", "origin": "seed", "support": 2, "rejected": 0,
     "when": {"source_type": "swiss_dxf", "kind": "room", "labelled": False, "numbered": False,
              "fixtures": [], "area_min": 0.0, "area_max": 0.5},
     "why": "tiny unlabelled, unnumbered outline with nothing inside"},
    {"id": "seed-bathroom", "label": "bathroom", "origin": "seed", "support": 2, "rejected": 0,
     "when": {"source_type": "swiss_dxf", "kind": "room", "labelled": False, "fixtures_any": ["wc", "bathtub", "shower"]},
     "why": "unlabelled room that contains a WC, bathtub or shower"},
]


def trusted(r: dict) -> bool:
    return confidence(r) >= TRUSTED and len(r.get("drawings", [])) >= MIN_DRAWINGS


def _confirm(r: dict, drawing: str):
    r["support"] += 1
    r.setdefault("drawings", [])
    if drawing not in r["drawings"]:
        r["drawings"].append(drawing)


def confidence(r: dict) -> float:
    # Laplace-style: 1 confirmation -> 0.67, 3 -> 0.8, 8 -> 0.9; each rejection pulls it down
    return round((r["support"] + 1) / (r["support"] + 2 * r["rejected"] + 2), 3)


def describe(r: dict) -> str:
    w = r["when"]
    parts = [w.get("kind", "element") + "s"]
    if w.get("labelled") is False:
        parts.append("without a name")
    if w.get("numbered") is False:
        parts.append("without a number")
    elif w.get("numbered") is True:
        parts.append("with a room number")
    if "fixtures" in w:
        parts.append("with nothing inside" if not w["fixtures"] else "containing " + "+".join(w["fixtures"]))
    if "fixtures_any" in w:
        parts.append("containing a " + " or ".join(w["fixtures_any"]))
    if "area_max" in w:
        parts.append(f"{w.get('area_min', 0):.2f}–{w['area_max']:.2f} m²")
    return f"{' '.join(parts)} → {LABELS.get(r['label'], {'text': r['label']})['text']}"


def load_rules() -> list[dict]:
    learned = json.loads(RULES_FILE.read_text()) if RULES_FILE.exists() else {"rules": [], "seed_state": {}}
    seeds = []
    for s in SEED:  # seed rules keep their support/rejections from reviews
        st = learned.get("seed_state", {}).get(s["id"], {})
        if not st.get("deleted"):
            seeds.append({**s, "support": st.get("support", s["support"]), "rejected": st.get("rejected", 0),
                          "drawings": st.get("drawings", [])})
    return seeds + learned["rules"]


def _save(rules: list[dict]):
    learned = {"rules": [r for r in rules if r["origin"] != "seed"],
               "seed_state": {r["id"]: {"support": r["support"], "rejected": r["rejected"], "drawings": r.get("drawings", [])} for r in rules if r["origin"] == "seed"}}
    old = json.loads(RULES_FILE.read_text()) if RULES_FILE.exists() else {}
    for k, v in old.get("seed_state", {}).items():  # remember deleted seeds
        if v.get("deleted"):
            learned["seed_state"][k] = v
    RULES_FILE.write_text(json.dumps(learned, indent=1, ensure_ascii=False))


def features(b: Building, e: Element, fx: list[tuple[str, Polygon]] | None = None) -> dict:
    inside = []
    if e.polygon and len(e.polygon) >= 3:
        poly = Polygon(e.polygon).buffer(0.05 if b.source_type != "raster" else 2)
        fx = fx if fx is not None else _fixtures(b)
        inside = sorted({s for s, p in fx if poly.contains(p.representative_point())} & WET)
    return {"source_type": b.source_type, "kind": e.kind, "labelled": bool(e.name), "numbered": bool(e.number),
            "fixtures": inside, "area": e.area_m2}


def _fixtures(b: Building) -> list[tuple[str, Polygon]]:
    return [(f.subtype, Polygon(f.polygon)) for f in b.elements
            if f.kind == "fixture" and f.polygon and len(f.polygon) >= 3]


def matches(w: dict, f: dict) -> bool:
    for k in ("source_type", "kind", "labelled", "numbered"):
        if k in w and w[k] != f[k]:
            return False
    if "fixtures" in w and w["fixtures"] != f["fixtures"]:
        return False
    if "fixtures_any" in w and not set(w["fixtures_any"]) & set(f["fixtures"]):
        return False
    if "area_max" in w and (f["area"] is None or not (w.get("area_min", 0) <= f["area"] <= w["area_max"])):
        return False
    return True


def _relabel(e: Element, label: str):
    tgt = LABELS.get(label, {"kind": "room", "subtype": label})
    e.kind, e.subtype = tgt["kind"], tgt["subtype"]
    e.flags = [f for f in e.flags if f != "room has no label"]


def reviews() -> dict[tuple[str, str], dict]:
    """Latest human decision per (drawing, element)."""
    out = {}
    if REVIEWS_FILE.exists():
        for line in REVIEWS_FILE.read_text().splitlines():
            r = json.loads(line)
            out[(r["drawing"], r["element"])] = r
    return out


def apply(b: Building, drawing: str | None = None) -> Building:
    """Raw extracted building -> building with rules and human decisions applied (returns a copy)."""
    b = b.model_copy(deep=True)
    rules = [r for r in load_rules() if confidence(r) >= 0.5]
    fx = _fixtures(b)
    raw = {e.id: (e.kind, e.subtype, list(e.flags), e.confidence) for e in b.elements}
    for e in b.elements:
        if e.kind not in ("room",):
            continue
        f = features(b, e, fx)
        for r in rules:
            if matches(r["when"], f):
                c = confidence(r)
                _relabel(e, r["label"])
                e.classified_by = r["id"]
                if not trusted(r):  # not trusted yet: a human should confirm
                    e.confidence = min(e.confidence, c)
                    e.flags.append(f"auto-classified as {LABELS.get(r['label'], {'text': r['label']})['text'].lower()} "
                                   f"(rule {c:.0%}, confirmed on {len(r.get('drawings', []))}/{MIN_DRAWINGS} drawings)")
                break
    key = drawing or b.source_file
    rv = {k[1]: v for k, v in reviews().items() if k[0] == key}
    for e in b.elements:
        d = rv.get(e.id)
        if not d:
            continue
        e.reviewed = d["decision"] if d["decision"] != "label" else f"label:{d['label']}"
        if d["decision"] == "label":
            _relabel(e, d["label"])
        if d["decision"] in ("ok", "label"):
            e.confidence, e.flags = 1.0, [f"confirmed by a reviewer ({time.strftime('%Y-%m-%d', time.localtime(d['t']))})"]
        elif d["decision"] == "no":  # the automatic classification was wrong: back to what was extracted
            e.kind, e.subtype, e.flags, e.confidence = raw[e.id]
            e.classified_by = None
            e.flags = e.flags + ["reviewer rejected the automatic classification: what is it?"]
    return b


def record(raw: Building, drawing: str, ids: list[str], decision: str, label: str | None = None) -> str:
    """Store a decision and learn from it. Returns a one-line summary of what was learned."""
    assert decision in ("ok", "no", "label")
    with _lock:
        REVIEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REVIEWS_FILE, "a") as fh:
            for i in ids:
                fh.write(json.dumps({"t": time.time(), "drawing": drawing, "element": i, "decision": decision,
                                     "label": label}) + "\n")
        rules = load_rules()
        by_id = {r["id"]: r for r in rules}
        current = apply(raw, drawing=None)  # rule classification before this decision (ignores old reviews)
        cur = {e.id: e for e in current.elements}
        rawi = {e.id: e for e in raw.elements}
        fx = _fixtures(raw)
        notes = []
        for i in ids:
            rule = by_id.get(cur[i].classified_by) if i in cur else None
            if rule and (decision == "ok" or (decision == "label" and label == rule["label"])):
                _confirm(rule, drawing)
            elif rule and decision in ("no", "label"):
                rule["rejected"] += 1
            if decision == "label" and i in rawi and not (rule and label == rule["label"]):
                f = features(raw, rawi[i], fx)
                notes.append(_learn(rules, f, label, drawing))
        _save(rules)
        touched = {by_id.get(cur[i].classified_by)["id"] for i in ids if i in cur and cur[i].classified_by in by_id}
        for rid in touched:
            r = by_id[rid]
            nd = len(r.get("drawings", []))
            notes.append(f"rule '{describe(r)}' now at {confidence(r):.0%}, confirmed on {nd} drawing{'s' * (nd != 1)}"
                         + (" — trusted, no longer needs review" if trusted(r) else
                            f" — needs confirmations on {MIN_DRAWINGS - nd} more drawing{'s' * (MIN_DRAWINGS - nd != 1)} before it is trusted"
                            if nd < MIN_DRAWINGS else ""))
    return "; ".join(dict.fromkeys(n for n in notes if n)) or "saved"


def _learn(rules: list[dict], f: dict, label: str, drawing: str) -> str:
    """Create a rule from one example, or widen an existing rule for the same label and signature."""
    sig = {k: f[k] for k in ("source_type", "kind", "labelled", "numbered", "fixtures")}
    for r in rules:
        if r["origin"] == "review" and r["label"] == label and all(r["when"].get(k) == v for k, v in sig.items()):
            w = r["when"]
            if f["area"] is not None:
                w["area_min"] = round(min(w.get("area_min", f["area"]), f["area"] * 0.75), 3)
                w["area_max"] = round(max(w.get("area_max", f["area"]), f["area"] * 1.25), 3)
            _confirm(r, drawing)
            return f"widened rule '{describe(r)}'"
    when = dict(sig)
    if f["area"] is not None:
        when.update(area_min=round(f["area"] * 0.75, 3), area_max=round(f["area"] * 1.25, 3))
    r = {"id": "rule-" + uuid.uuid4().hex[:8], "label": label, "origin": "review", "support": 1, "rejected": 0, "drawings": [drawing],
         "when": when, "why": "learned from a review", "created": time.time()}
    rules.append(r)
    return f"learned rule '{describe(r)}'"


def delete_rule(rule_id: str) -> bool:
    with _lock:
        rules = load_rules()
        if not any(r["id"] == rule_id for r in rules):
            return False
        old = json.loads(RULES_FILE.read_text()) if RULES_FILE.exists() else {"rules": [], "seed_state": {}}
        if rule_id.startswith("seed-"):
            old.setdefault("seed_state", {})[rule_id] = {"deleted": True}
        else:
            old["rules"] = [r for r in old.get("rules", []) if r["id"] != rule_id]
        RULES_FILE.write_text(json.dumps(old, indent=1, ensure_ascii=False))
        return True


def listing() -> list[dict]:
    return [{**r, "confidence": confidence(r), "trusted": trusted(r), "n_drawings": len(r.get("drawings", [])), "text": describe(r)} for r in load_rules()]
