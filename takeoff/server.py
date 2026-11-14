"""Web app: projects, plan viewer, 3D, chat. Every number shown comes from the takeoff engine.

    uv run uvicorn takeoff.server:app --port 8765
"""

from __future__ import annotations

import collections
import faulthandler
import signal
import json
import math
import re
import shutil
from functools import lru_cache
from pathlib import Path

import ezdxf  # import on the main thread: a first import inside a request thread deadlocks
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import engine, llm, pipeline, rules
from .questions import Query

ROOT = Path(__file__).resolve().parent.parent
DATASET = Path.home() / "Downloads/junction-dataset"
UPLOADS = ROOT / "data_cache" / "uploads"
WEB = Path(__file__).resolve().parent / "web"

faulthandler.register(signal.SIGUSR1)  # `kill -USR1 <pid>` dumps all thread stacks
app = FastAPI(title="Stoa takeoff")


def _rel(p: Path) -> str:
    return str(p)


@lru_cache(maxsize=1)
def projects() -> list[dict]:
    out = []
    cache = ROOT / "data_cache" / "buildings"
    for f in sorted(cache.glob("swiss_dwellings__*.json"))[:40]:
        stem = f.stem.split("__", 1)[1]
        out.append({"path": str(DATASET / "data/swiss_dwellings" / f"{stem}.png"), "name": stem.replace("_", " "),
                    "group": "Swiss apartments (DXF + PDF)", "format": "DXF"})
    for f in sorted(cache.glob("ifc_models__*.json")):
        stem = f.stem.split("__", 1)[1]
        out.append({"path": str(DATASET / "data/ifc_models" / f"{stem}.ifc"), "name": stem,
                    "group": "BIM models (IFC)", "format": "IFC"})
    ann = ROOT / "data_cache" / "cubicasa_annotations.json"
    if ann.exists():
        test = sorted(k for k, v in json.loads(ann.read_text()).items() if v["split"] == "test")
        for k in test[:40]:
            out.append({"path": str(DATASET / "data/cubicasa5k" / f"{k}.png"), "name": f"Finnish plan {k}",
                        "group": "Scanned plans (raster)", "format": "Scan"})
    for f in sorted(UPLOADS.glob("*")) if UPLOADS.exists() else []:
        if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".dxf", ".ifc"):
            out.append({"path": str(f), "name": f.name, "group": "Uploaded", "format": f.suffix[1:].upper()})
    return out


def _check(path: str) -> Path:
    p = Path(path).resolve()
    if not (p.is_relative_to(DATASET.resolve()) or p.is_relative_to(UPLOADS.resolve())):
        raise HTTPException(403, "path outside the dataset")
    return p


@lru_cache(maxsize=16)
def _raw(path: str):
    b = pipeline.load_raw(path)
    if b is None:
        raise HTTPException(422, "No extractor for this drawing type yet")
    return b


def _building(path: str):
    """Raw extraction (cached) + current rules and reviewer decisions (cheap, always fresh)."""
    return rules.apply(_raw(path), drawing=path)


def summary(b) -> dict:
    rows = collections.Counter()
    area = collections.defaultdict(float)
    for e in b.elements:
        if e.kind in ("floor", "space_label") or (e.kind == "other" and e.subtype != "shaft"):
            continue
        key = (e.kind, e.subtype if e.kind in ("fixture", "room", "other") else None)
        rows[key] += 1
        if e.area_m2:
            area[key] += e.area_m2
    return {"rows": [{"kind": k, "subtype": s, "count": n, "area_m2": round(area[(k, s)], 2) if area[(k, s)] else None}
                     for (k, s), n in sorted(rows.items(), key=lambda x: (x[0][0], x[0][1] or ""))],
            "flagged": sum(1 for e in b.elements if e.flags),
            "elements": len(b.elements)}


@app.get("/api/projects")
def api_projects():
    return projects()


@app.get("/api/building")
def api_building(path: str):
    _check(path)
    b = _building(path)
    vector = b.source_type != "raster"
    d = b.model_dump()
    d["summary"] = summary(b)
    d["view"] = {"flip_y": vector, "units": "m" if vector else "px",
                 "background": f"/api/background?path={path}" if b.source_type in ("raster", "swiss_dxf") else None,
                 "background_kind": "image" if b.source_type == "raster" else ("vector" if b.source_type == "swiss_dxf" else None)}
    if b.source_type == "raster":
        import cv2
        h, w = cv2.imread(b.source_file, cv2.IMREAD_GRAYSCALE).shape[:2]
        d["view"]["image_size"] = [w, h]
    d["interpreter"] = "claude" if llm.os.environ.get("ANTHROPIC_API_KEY") else "keyword parser"
    return JSONResponse(d)


@lru_cache(maxsize=32)
def _dxf_paths(dxf: str) -> dict:
    """DXF linework as SVG path strings per layer (y flipped), plus wall polygons for the 3D view."""
    doc = ezdxf.readfile(dxf)
    layers: dict[str, list[str]] = collections.defaultdict(list)
    texts, walls = [], []

    def pts_d(pts, closed):
        if len(pts) < 2:
            return None
        s = "M" + " L".join(f"{x:.3f} {-y:.3f}" for x, y in pts)
        return s + (" Z" if closed else "")

    for e in doc.modelspace():
        t, lay = e.dxftype(), e.dxf.layer
        try:
            if t == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points("xy")]
                d = pts_d(pts, e.closed)
                if d:
                    layers[lay].append(d)
                if lay == "WALL" and e.closed and len(pts) >= 3:
                    walls.append(pts)
            elif t == "LINE":
                layers[lay].append(pts_d([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)], False))
            elif t == "ARC":
                pts = [(p.x, p.y) for p in e.flattening(0.02)]
                layers[lay].append(pts_d(pts, False))
            elif t == "CIRCLE":
                c, r = e.dxf.center, e.dxf.radius
                pts = [(c.x + r * math.cos(a / 24 * 2 * math.pi), c.y + r * math.sin(a / 24 * 2 * math.pi)) for a in range(24)]
                layers[lay].append(pts_d(pts, True))
            elif t == "HATCH":
                for bp in e.paths:
                    if hasattr(bp, "vertices"):
                        pts = [(v[0], v[1]) for v in bp.vertices]
                        if len(pts) >= 3:
                            layers[lay].append(pts_d(pts, True))
                            if lay == "WALL":
                                walls.append(pts)
            elif t == "TEXT" and lay != "ROOM_TEXT":
                texts.append({"x": e.dxf.insert.x, "y": -e.dxf.insert.y, "h": e.dxf.height, "t": e.dxf.text})
        except Exception:
            continue
    return {"layers": {k: [d for d in v if d] for k, v in layers.items()}, "texts": texts, "walls": walls}


@app.get("/api/background")
def api_background(path: str):
    p = _check(path)
    b = _building(path)
    if b.source_type == "raster":
        return FileResponse(b.source_file)
    if b.source_type == "swiss_dxf":
        return JSONResponse(_dxf_paths(b.source_file))
    raise HTTPException(404, "no background for this source")


@app.get("/api/original")
def api_original(path: str):
    """The drawing as delivered (PNG/PDF), for side-by-side checking."""
    p = _check(path)
    for cand in (p.with_suffix(".png"), p.with_suffix(".pdf"), p):
        if cand.exists() and cand.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf"):
            return FileResponse(cand)
    raise HTTPException(404)


class Ask(BaseModel):
    path: str
    question: str
    history: list[dict] = []
    height_m: float | None = None


@app.post("/api/ask")
def api_ask(req: Ask):
    _check(req.path)
    b = _building(req.path)
    interp, who = llm.interpret(b, req.question, req.history)
    if not interp.understood or interp.query is None:
        return {"understood": False, "message": interp.clarification or "I could not map that to a takeoff query.",
                "interpreter": who}
    q: Query = interp.query
    # only a height the user changed counts as stated; the default stays a flagged assumption
    if req.height_m and abs(req.height_m - engine.DEFAULT_HEIGHT_M) > 1e-6 and q.op == "wall_area" and not q.height_m:
        q.height_m = req.height_m
    a = engine.run(b, q)
    return {"understood": True, "interpreter": who, "note": interp.note,
            "query": q.model_dump(exclude_defaults=True), "answer": a.model_dump()}


class Review(BaseModel):
    path: str
    ids: list[str]
    decision: str            # ok | no | label
    label: str | None = None


@app.post("/api/review")
def api_review(req: Review):
    _check(req.path)
    if req.decision not in ("ok", "no", "label") or (req.decision == "label" and not req.label):
        raise HTTPException(400, "decision must be ok, no, or label with a label")
    label = re.sub(r"[^a-z0-9_]+", "_", req.label.strip().lower()) if req.label else None
    learned = rules.record(_raw(req.path), req.path, req.ids, req.decision, label)
    return {"learned": learned}


@app.get("/api/rules")
def api_rules():
    return {"rules": rules.listing(), "labels": {k: v["text"] for k, v in rules.LABELS.items()}}


@app.delete("/api/rules/{rule_id}")
def api_delete_rule(rule_id: str):
    if not rules.delete_rule(rule_id):
        raise HTTPException(404, "no such rule")
    return {"ok": True}


@app.post("/api/upload")
async def api_upload(file: UploadFile):
    name = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "drawing")
    if Path(name).suffix.lower() not in (".png", ".jpg", ".jpeg", ".dxf", ".ifc", ".pdf"):
        raise HTTPException(415, "Upload a PNG, JPG, PDF, DXF or IFC file")
    UPLOADS.mkdir(parents=True, exist_ok=True)
    dst = UPLOADS / name
    with open(dst, "wb") as f:
        shutil.copyfileobj(file.file, f)
    if dst.suffix.lower() == ".pdf":  # scanned/vector PDF -> raster page 1 for the symbol detector
        import fitz
        page = fitz.open(dst)[0]
        png = dst.with_suffix(".png")
        page.get_pixmap(dpi=150).save(png)
        dst = png
    projects.cache_clear()
    return {"path": str(dst)}


@app.middleware("http")
async def no_stale_ui(request, call_next):
    # browsers must revalidate the UI files, otherwise an old app.js keeps running after an update
    resp = await call_next(request)
    if not request.url.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-cache"
    return resp


app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
