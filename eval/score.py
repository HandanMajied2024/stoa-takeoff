"""Score the pipeline against questions.jsonl with the challenge rules:
counts must be exact; areas, lengths and volumes within 2%.

    uv run python -m eval.score --dataset ~/Downloads/junction-dataset --source swiss_dwellings --files 200
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from takeoff import engine, pipeline, questions  # noqa: E402


def correct(pred, q) -> bool:
    if pred is None:
        return False
    a = q["answer"]
    if q["type"] == "count":
        return round(pred) == a
    if q["type"] in ("area", "length", "volume"):
        return abs(pred - a) <= 0.02 * abs(a) + 1e-9
    return False


def solve_file(dataset: str, path: str, qs: list[dict]) -> list[dict]:
    out = []
    try:
        b = pipeline.load(Path(dataset) / path)
    except Exception as ex:  # extractor crash: every question on this file is a miss
        return [{**q, "pred": None, "ok": False, "why": f"extract: {type(ex).__name__}: {ex}"[:200]} for q in qs]
    for q in qs:
        pred, why = None, ""
        if b is None:
            why = "no extractor for this source yet"
        else:
            query = questions.parse(q["question"])
            if query is None:
                why = "question not understood"
            else:
                try:
                    ans = engine.run(b, query)
                    pred = ans.value
                    why = "" if pred is not None else "; ".join(ans.flags)
                except Exception as ex:
                    why = f"engine: {type(ex).__name__}: {ex}"[:200]
        out.append({**q, "pred": pred, "ok": correct(pred, q), "why": why})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(Path.home() / "Downloads/junction-dataset"))
    ap.add_argument("--source", action="append", help="limit to these sources (repeatable)")
    ap.add_argument("--files", type=int, default=0, help="sample N drawings per source (0 = all)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cubicasa-split", default="test",
                    help="only score CubiCasa plans from this official split (train/val were used for training)")
    args = ap.parse_args()

    split_of = {}
    ann = ROOT / "data_cache" / "cubicasa_annotations.json"
    if ann.exists():
        split_of = {k: v["split"] for k, v in json.loads(ann.read_text()).items()}
    by_file: dict[str, list[dict]] = collections.defaultdict(list)
    for line in open(Path(args.dataset) / "questions.jsonl"):
        q = json.loads(line)
        src = q["path"].split("/")[1]
        if q["type"] == "text" or (args.source and src not in args.source):
            continue
        if src == "cubicasa5k" and args.cubicasa_split != "all" and \
                split_of.get(Path(q["path"]).stem) != args.cubicasa_split:
            continue
        by_file[q["path"]].append(q)

    files = list(by_file)
    if args.files:
        rnd = random.Random(args.seed)
        per_src = collections.defaultdict(list)
        for f in files:
            per_src[f.split("/")[1]].append(f)
        files = [f for fs in per_src.values() for f in rnd.sample(fs, min(args.files, len(fs)))]

    t0 = time.time()
    results = []
    with ProcessPoolExecutor(args.workers) as ex:
        futs = [ex.submit(solve_file, args.dataset, f, by_file[f]) for f in files]
        for i, fu in enumerate(as_completed(futs), 1):
            results.extend(fu.result())
            if i % 200 == 0:
                print(f"  {i}/{len(files)} drawings", file=sys.stderr)

    tab = collections.defaultdict(lambda: [0, 0])
    for r in results:
        for key in (("ALL", ""), (r["path"].split("/")[1], ""), (r["path"].split("/")[1], r["type"])):
            tab[key][0] += r["ok"]
            tab[key][1] += 1
    print(f"\n{'source':<18}{'type':<8}{'correct':>9}{'total':>8}{'acc':>8}")
    for (s, t), (ok, n) in sorted(tab.items()):
        print(f"{s:<18}{t:<8}{ok:>9}{n:>8}{ok / n:>8.1%}")
    print(f"\n{len(files)} drawings, {time.time() - t0:.0f}s")

    out = ROOT / "eval" / "failures.jsonl"
    with open(out, "w") as f:
        for r in results:
            if not r["ok"]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    why = collections.Counter(r["why"].split(":")[0] for r in results if not r["ok"])
    print("failure reasons:", why.most_common(8))
    print(f"failures written to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
