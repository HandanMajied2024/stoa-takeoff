# Stoa takeoff

Construction drawings → a traceable building model → exact quantities.

Code does every count and measurement, and each number points back to the drawing element it came
from. The LLM (Claude) only translates a chat question into a query; the engine computes the answer.

## Run

```bash
uv sync
uv run uvicorn takeoff.server:app --port 8765                  # web app: http://localhost:8765
export ANTHROPIC_API_KEY=...                                   # optional: Claude reads chat questions (else keyword parser)
uv run python -m eval.score                                   # full benchmark
uv run python -m eval.score --source swiss_dwellings --files 200
uv run python -m takeoff.ask <drawing> "How many toilets (WC) are drawn on this floor plan?"
```

`--dataset` defaults to `~/Downloads/junction-dataset`. Failed questions are written to
`eval/failures.jsonl`.

## Layout

| Path | What it does |
|---|---|
| `takeoff/model.py` | Building model: rooms, doors, windows, fixtures, walls… each with a polygon, quantities, source reference, confidence and flags |
| `takeoff/extractors/swiss_dxf.py` | Layered CAD plans: room polygons with shafts/voids removed, door leaves, window frames, fixture symbols classified by their drawn parts |
| `takeoff/extractors/ifc.py` | BIM: IFC base quantities (unit-converted), with geometry as fallback and cross-check; layer parts and stair components handled |
| `takeoff/questions.py` | Multilingual question → `Query` (10 languages) |
| `takeoff/engine.py` | Deterministic `Query` → `Answer` with a step-by-step trace and flags |
| `takeoff/pipeline.py` | Picks the best file for a drawing (DXF/IFC over PDF/PNG) and caches the extracted model |
| `takeoff/rules.py` | Review learning loop: reviewer labels become rules (signature → label) that apply to every drawing and earn trust with confirmations; stored in `models/learned_rules.json`, decisions in `data_cache/reviews.jsonl` |
| `takeoff/llm.py` | Chat question → `Query` with Claude (structured output, building vocabulary as context); keyword fallback |
| `takeoff/server.py` + `takeoff/web/` | Web app: projects, plan viewer with every element clickable, 3D extrusion (assumed height, flagged), chat with "How it was calculated", takeoff table + CSV, review queue; works on phones |
| `eval/score.py` | Scoring rules: counts exact, areas/lengths/volumes within 2% |

## Benchmark (questions.jsonl, 126,208 non-text questions)

| Source | Accuracy | Status |
|---|---|---|
| swiss_dwellings (37,584) | **99.3%** | DXF extractor |
| ifc_models (3,062) | **99.5%** | IFC extractor |
| cubicasa5k (6,796 on the 387 held-out test plans) | **78.7%** | YOLO11s symbol detector (14 classes) + OCR label cross-check |
| opening_design (48) | 0% | next: PDF schedule tables |

CubiCasa: the answer key is derived from the dataset's own SVG annotations, which we also train on, so
the score is reported only on the official **test split** (never seen in training or threshold tuning).
Training: `eval/cubicasa_svg.py` → `eval/build_yolo.py` → `eval/train_yolo.py` (25 epochs, imgsz 1024, M1
Max, val mAP50 0.805) → `eval/tune_thresholds.py` (per-class confidence cut-offs on the val split).
Per question type on val: saunas 95%, kitchens 94%, WC seats 93%, floors 92%, bedrooms/bathrooms/WC
rooms 88–91%, balconies 87%, sinks 83%, showers+bathtubs 72%, doors 65%, windows 55%. Exact counts of
thin, numerous symbols (windows, doors) remain the hard part; every low-confidence detection is flagged.
Published VLM baselines on similar counting tasks score ~34–55%.

## Web app

`uv run uvicorn takeoff.server:app --port 8765`, then open http://localhost:8765. Run it from a terminal:
an app sandbox without Downloads access will hang reading the dataset. Put `ANTHROPIC_API_KEY=...` in a
`.env` file (git-ignored) to let Claude read chat questions.

### Hosted demo (Vercel)

The full pipeline needs PyTorch, IfcOpenShell and the dataset, which do not fit a serverless function. The
demo ships 22 pre-extracted drawings and runs only the light parts (chat, engine, rules, reviews):

```bash
uv run python -m deploy.build_demo        # -> dist/vercel (no local paths, ~5 MB)
cd dist/vercel && vercel deploy --prod
```

Set `ANTHROPIC_API_KEY` in the Vercel project's environment variables. Questions are rate-limited
(`TAKEOFF_ASK_PER_HOUR`, `TAKEOFF_ASK_PER_DAY`); reviews and learned rules reset when an instance restarts.
Data and model licences: [DATA_LICENSES.md](DATA_LICENSES.md).

## Things we learned from the data

- **IFC room areas:** the areas stored in the model can be wrong. Duplex Foyer: 17.94 m² stored vs 15.59 m² from geometry, and geometry matches the answer key. Wall/slab base quantities (`Qto_*BaseQuantities`) are correct, but some models store them in mm.
- **Molio model:**
  - Walls and slabs are split into layer parts.
  - Every stair riser and tread is its own `IfcStair`; only the top-level stairs count.
- **Swiss plans:**
  - Some print the area next to the room name. It is kept as `written_area_m2` and checked against the measured area.
  - An apartment's area excludes balconies and the shared stairwell and lift.
