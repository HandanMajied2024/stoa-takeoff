"""Build the hosted demo bundle in dist/vercel (deploy with `vercel deploy --prod` from that folder).

The full pipeline needs PyTorch, IfcOpenShell, OpenCV and the 10 GB dataset, which do not fit a Vercel
function. So drawings are extracted here, shipped as data, and only the light parts run in the cloud:
question interpretation (Claude), the deterministic engine, rules and reviews.

    uv run python -m deploy.build_demo
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from takeoff import pipeline, server  # noqa: E402

DATA = Path.home() / "Downloads/junction-dataset/data"
OUT = ROOT / "dist" / "vercel"

SWISS = ["site1000_bldg2082_floor9385", "site1001_bldg2083_floor9389", "site1002_bldg2084_floor9393",
         "site1003_bldg2085_floor50930", "site1004_bldg2086_floor9400", "site1005_bldg2087_floor9545",
         "site1006_bldg2088_floor9498", "site1008_bldg2090_floor46975", "site1009_bldg2091_floor9508",
         "site1014_bldg2093_floor9444"]
IFC = {  # openly licensed models only (the buildingSMART samples are CC BY-ND, so they are left out)
    "kit-fzk-haus_ac20-fzk-haus": "FZK-Haus, KIT Institute for Automation and Applied Informatics (free use)",
    "bimspeed-gdynia_ruchu-oporu-18": "BIM-Speed Gdynia house, Garcia & Hartmann 2022, TU Berlin, CC BY 4.0",
    "bimspeed-vitoria_ald26-project": "BIM-Speed Vitoria ALD26, Garcia & Hartmann 2022, TU Berlin, CC BY 4.0",
    "kit-institute_ac20-institute-var-2": "AC20 Institute, KIT Institute for Automation and Applied Informatics (free use)",
}
SCANS = ["colorful-11260", "colorful-11395", "colorful-11397", "colorful-11398", "colorful-11400",
         "colorful-11485", "colorful-11527", "colorful-11565"]
SWISS_CREDIT = "Swiss Dwellings v3.0.0, Archilyse AG (doi:10.5281/zenodo.7788422), CC BY 4.0"
SCAN_CREDIT = "CubiCasa5K, (c) 2019 CubiCasa, CC BY-NC-SA 4.0 (non-commercial)"

PY = ["__init__.py", "model.py", "engine.py", "questions.py", "llm.py", "rules.py", "pipeline.py", "server.py"]

APP = '''"""Vercel entrypoint: the takeoff web app in demo mode (prepared drawings shipped in ./demo)."""
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("TAKEOFF_DEMO_DIR", str(HERE / "demo"))
# the function filesystem is read-only except /tmp: reviews and learned rules live there (reset on cold start)
os.environ.setdefault("TAKEOFF_RULES_FILE", "/tmp/learned_rules.json")
os.environ.setdefault("TAKEOFF_REVIEWS_FILE", "/tmp/reviews.jsonl")
if not Path(os.environ["TAKEOFF_RULES_FILE"]).exists():
    shutil.copy(HERE / "demo" / "learned_rules.json", os.environ["TAKEOFF_RULES_FILE"])

from takeoff.server import app  # noqa: E402,F401
'''

REQS = "fastapi>=0.115\npydantic>=2.7\nshapely>=2.0\nanthropic>=2.8\npython-multipart>=0.0.9\n"


def scrub(b, drawing_id: str):
    """No local paths in anything published."""
    b.source_file = drawing_id
    for e in b.elements:
        e.source.file = drawing_id
    return b


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "takeoff").mkdir(parents=True)
    for f in PY:
        shutil.copy(ROOT / "takeoff" / f, OUT / "takeoff" / f)
    shutil.copytree(ROOT / "takeoff" / "web", OUT / "takeoff" / "web")
    (OUT / "app.py").write_text(APP)
    (OUT / "requirements.txt").write_text(REQS)
    (OUT / "vercel.json").write_text(json.dumps({"$schema": "https://openapi.vercel.sh/vercel.json",
                                                 "functions": {"app.py": {"maxDuration": 120}}}, indent=1))
    demo = OUT / "demo"
    (demo / "buildings").mkdir(parents=True)
    (demo / "bg").mkdir()
    projects = []

    def add(path: Path, did: str, name: str, group: str, fmt: str, credit: str):
        b = pipeline.load_raw(path)
        if b is None:
            print("skip", path)
            return None
        file = did.replace("/", "__")
        (demo / "buildings" / f"{file}.json").write_text(scrub(b, did).model_dump_json())
        p = {"path": did, "file": file, "name": name, "group": group, "format": fmt, "credit": credit}
        projects.append(p)
        return b, file, p

    for s in SWISS:
        r = add(DATA / "swiss_dwellings" / f"{s}.png", f"swiss_dwellings/{s}.png", s.replace("_", " "),
                "Swiss apartments (DXF)", "DXF", SWISS_CREDIT)
        if r:
            (demo / "bg" / f"{r[1]}.json").write_text(json.dumps(server._dxf_paths(str(DATA / "swiss_dwellings" / f"{s}.dxf"))))
    for m, credit in IFC.items():
        add(DATA / "ifc_models" / f"{m}.ifc", f"ifc_models/{m}.ifc", m, "BIM models (IFC)", "IFC", credit)
    import cv2
    for k in SCANS:
        img = DATA / "cubicasa5k" / f"{k}.png"
        r = add(img, f"cubicasa5k/{k}.png", f"Finnish plan {k}", "Scanned plans (raster)", "Scan", SCAN_CREDIT)
        if r:
            shutil.copy(img, demo / "bg" / f"{r[1]}.png")
            h, w = cv2.imread(str(img), cv2.IMREAD_GRAYSCALE).shape[:2]
            r[2]["image_size"] = [w, h]

    (demo / "manifest.json").write_text(json.dumps({"projects": projects}, indent=1))
    shutil.copy(ROOT / "models" / "learned_rules.json", demo / "learned_rules.json")
    shutil.copy(ROOT / "DATA_LICENSES.md", OUT / "DATA_LICENSES.md")
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    leaks = [str(f) for f in OUT.rglob("*") if f.is_file() and f.suffix in (".json", ".py", ".js", ".html")
             and str(Path.home()) in f.read_text(errors="ignore")]
    print(f"{len(projects)} drawings, {size / 1e6:.1f} MB -> {OUT}")
    if leaks:
        sys.exit(f"local paths found in: {leaks}")


if __name__ == "__main__":
    main()
