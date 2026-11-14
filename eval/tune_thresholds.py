"""Tune per-class detector confidence thresholds for exact counts on the CubiCasa VAL split.

Writes models/cubicasa_thresholds.json. The test split is never touched here.
"""

import collections
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from takeoff.extractors import raster  # noqa: E402
from takeoff.questions import parse  # noqa: E402

IMAGES = Path.home() / "Downloads/junction-dataset/data/cubicasa5k"
GRID = [round(0.1 + 0.05 * i, 2) for i in range(16)]

# question key -> how the count is formed from per-class detection counts
RULES = {
    ("door", None): lambda c: c["door"],
    ("window", None): lambda c: c["window"],
    ("fixture", "wc"): lambda c: c["toilet"],
    ("fixture", "sink_any"): lambda c: c["sink"],
    ("fixture", "bath_or_shower"): lambda c: c["shower"] + c["bathtub"],
    ("floor", None): lambda c: max(1, c["floorplan"]),
    ("room", "bedroom"): lambda c: c["bedroom"],
    ("room", "kitchen"): lambda c: c["kitchen"],
    ("room", "bathroom"): lambda c: c["bath"],
    ("room", "wc"): lambda c: c["wc_room"],
    ("room", "balcony"): lambda c: c["balcony"],
    ("room", "sauna"): lambda c: max(c["sauna_stove"], c["sauna_room"]),
}
DEPENDS = {k: set() for k in RULES}


def main(split="val"):
    ann = json.loads((ROOT / "data_cache/cubicasa_annotations.json").read_text())
    keys = [k for k, v in ann.items() if v["split"] == split and (IMAGES / f"{k}.png").exists()]
    gt = collections.defaultdict(dict)
    for line in open(IMAGES.parent.parent / "questions.jsonl"):
        q = json.loads(line)
        if "cubicasa" in q["path"] and q["question"].isascii() and Path(q["path"]).stem in keys:
            x = parse(q["question"])
            gt[Path(q["path"]).stem][(x.kind, x.subtype)] = q["answer"]
    dets = {}
    for i, k in enumerate(keys):
        dets[k] = raster.detect(IMAGES / f"{k}.png")
        if i % 100 == 0:
            print(f"detect {i}/{len(keys)}", file=sys.stderr)
    classes = sorted({d["cls"] for v in dets.values() for d in v} | {"door", "window"})

    def acc(th, qkeys):
        ok = n = 0
        for k in keys:
            cnt = collections.Counter(d["cls"] for d in dets[k] if d["conf"] >= th.get(d["cls"], 0.35))
            for qk in qkeys:
                if qk in gt[k]:
                    n += 1
                    ok += RULES[qk](cnt) == gt[k][qk]
        return ok / max(n, 1), n

    th = {c: 0.35 for c in classes}
    # each question depends on a few classes: tune them jointly per question (small grids)
    groups = {
        ("door", None): ["door"], ("window", None): ["window"], ("fixture", "wc"): ["toilet"],
        ("fixture", "sink_any"): ["sink"], ("fixture", "bath_or_shower"): ["shower", "bathtub"],
        ("floor", None): ["floorplan"], ("room", "bedroom"): ["bedroom"], ("room", "kitchen"): ["kitchen"],
        ("room", "bathroom"): ["bath"], ("room", "wc"): ["wc_room"], ("room", "balcony"): ["balcony"],
        ("room", "sauna"): ["sauna_stove", "sauna_room"],
    }
    report = {}
    for qk, cls in groups.items():
        before = acc(th, [qk])[0]
        best = (before, tuple(th[c] for c in cls))
        for combo in itertools.product(GRID, repeat=len(cls)):
            trial = {**th, **dict(zip(cls, combo))}
            a = acc(trial, [qk])[0]
            if a > best[0] + 1e-9:
                best = (a, combo)
        th.update(dict(zip(cls, best[1])))
        report[str(qk)] = {"val_acc": round(best[0], 4), "n": acc(th, [qk])[1], "thresholds": dict(zip(cls, best[1]))}
        print(qk, f"{before:.1%} -> {best[0]:.1%}", dict(zip(cls, best[1])))
    out = ROOT / "models/cubicasa_thresholds.json"
    out.write_text(json.dumps(th, indent=1))
    (ROOT / "models/cubicasa_val_report.json").write_text(json.dumps(report, indent=1))
    print("overall val accuracy:", f"{acc(th, list(RULES))[0]:.1%}", "->", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
