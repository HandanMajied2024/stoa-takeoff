# Open-source repos, models and datasets for raster floor plan and scanned-drawing understanding (as of Nov 2026)

Scope: tools you could use in a 2-3 day hackathon to count symbols (doors, windows, WC, sinks, showers, bathtubs, saunas, stairs), segment rooms, OCR room labels and areas (including Finnish abbreviations), turn raster plans into vectors, and cope with low-resolution, rotated or hand-drawn scans.

How to read this file: every line under "Cited Findings" was checked against the linked source during this research session (about 15 tool calls). Lines under "Inferences" or "Gaps" marked **[prior knowledge, unverified]** come from the researcher's background knowledge and were NOT re-checked. Confirm them before relying on them.

## 1. CubiCasa5k: the official repo, its models and their accuracy, and the SVG annotations

### Takeaway
CubiCasa5k is still the only large public raster plan dataset with symbol labels that is mostly Finnish, which makes it the best fit for this domain. The official multi-task model (rooms, icons and wall/opening heatmaps) has downloadable weights but runs on an old PyTorch 1.0 stack. Its test mIoU is about 57.5% for rooms and 55.7% for icons, so it is a weak baseline, not a production model. The data is licensed CC BY-NC-SA 4.0, which means non-commercial use only. The SVG annotations hold far more detail than the 12 room and 11 icon classes used for training: they include 65 room types and 52 icon types, among them Shower, SaunaBench and SaunaStove, WashingMachine and Stairs.

### Cited Findings
**Official repo**
- github.com/CubiCasa/CubiCasa5k has about 630 stars and only 13 commits, so it is effectively unmaintained. It requires Python 3.6.5, PyTorch 1.0.0 and CUDA, with Docker (nvidia-docker2) optional. Pretrained weights `model_best_val_loss_var.pkl` are on Google Drive (https://drive.google.com/file/d/1gRB7ez1e4H7a9Y09lLqRuna0luZO5VRK/view). You evaluate with `python eval.py --weights ...`. Training first needs `create_lmdb.py`, which builds an LMDB of about 105 GB. — [CubiCasa5k GitHub](https://github.com/CubiCasa/CubiCasa5k)
- The dataset is on Zenodo as `cubicasa5k.zip` (5.5 GB), licensed CC BY-NC-SA 4.0 and published 28 March 2019. — [Zenodo record 2613548](https://zenodo.org/records/2613548)

**Dataset composition**
- There are 5,000 plans, chosen from about 15,000 mostly Finnish floor plan images. They fall into three categories: high-quality architectural (3,732), high-quality (992) and colourful (276). The split is random: 4,200 train, 400 val and 400 test. The annotations are polygons covering "over 80 floorplan object categories". — [CubiCasa5k paper (ar5iv)](https://ar5iv.labs.arxiv.org/html/1904.01920); [arXiv 1904.01920](https://arxiv.org/abs/1904.01920)

**Classes used in the experiments**
- Rooms (12): Background, Outdoor, Wall, Kitchen, Living Room, Bedroom, Bath, Hallway, Railing, Storage, Garage, Other rooms.
- Icons (11): Empty, Window, Door, Closet, Electrical Appliance, Toilet, Sink, Sauna bench, Fire Place, Bathtub, Chimney.
- Source: [CubiCasa5k paper Table 6](https://ar5iv.labs.arxiv.org/html/1904.01920)

**Reported accuracy (Table 5)**

"Raw" means the pixel segmentation; "polygonized" means the output after post-processing into polygons.

| Output | Overall accuracy | Mean accuracy | mIoU |
|---|---|---|---|
| Rooms, raw, test | 82.7 | 69.8 | 57.5 |
| Rooms, polygonized, test | 77.3 | 61.6 | 49.3 |
| Icons, raw, test | 97.6 | 61.5 | 55.7 |
| Icons, polygonized, test | 96.7 | 45.3 | 41.6 |

- The val column for polygonized icons reports mean accuracy as 94.8, which looks like a typo. Source: [paper](https://ar5iv.labs.arxiv.org/html/1904.01920)

**Per-class test IoU, raw segmentation (Table 6)**

| Class | IoU | | Class | IoU |
|---|---|---|---|---|
| Wall | 73.0 | | Window | 66.8 |
| Kitchen | 65.0 | | Door | 53.6 |
| Living room | 66.6 | | Closet | 69.2 |
| Bedroom | 74.2 | | Electrical appliance | 66.0 |
| Bath | 60.6 | | Toilet | 62.8 |
| Hallway | 55.6 | | Sink | 55.7 |
| Storage | 44.8 | | Sauna bench | 67.3 |
| Railing | 23.6 | | Fireplace | 36.2 |
| Garage | 33.7 | | Bathtub | 26.7 |
| Other rooms | 41.4 | | Chimney | 11.2 |

- Source: [paper](https://ar5iv.labs.arxiv.org/html/1904.01920)

**What the SVG annotations contain (from the loader `floortrans/loaders/house.py`)**
- Each `<g>` element is classified in one of three ways:
  - `id="Wall"` or `id="Railing"` produces wall polygons.
  - `id="Window"` or `id="Door"` produces opening polygons.
  - `class="FixedFurniture <IconName> ..."` produces fixtures. The loader keeps only 4-corner icons.
- `class="Space <RoomName> ..."` marks rooms.
- A commented-out parser exists for `Stairs`, with `Flight` and `Winding` children. That means stairs are annotated in the SVGs but the official loader ignores them.
- All class names are in English, not Finnish.
- Source: [house.py](https://raw.githubusercontent.com/CubiCasa/CubiCasa5k/master/floortrans/loaders/house.py)

**Full room vocabulary (65 types, `all_rooms`)**
- The vocabulary includes Bath, Bedroom, Closet, DraughtLobby, DressingRoom, Entry, Garage, HallWay, Kitchen, LivingRoom, Outdoor, Sauna, StairWell, Stairs, Storage, TechnicalRoom, Utility, Railing, Wall, Undefined and UserDefined.
- The training remap collapses Bath + Sauna into Bath, and Closet + DressingRoom + Storage into Storage. — [house.py](https://raw.githubusercontent.com/CubiCasa/CubiCasa5k/master/floortrans/loaders/house.py)

**Full icon vocabulary (52 types, `all_icons`)**
- Openings: Window, Door.
- Bath fixtures: Bathtub, BathtubRound, Shower, ShowerCab, ShowerScreen (plus round variants), ShowerPlatform, Toilet, Urinal, Jacuzzi.
- Sinks: Sink, CornerSink, DoubleSink, RoundSink, SideSink, WaterTap.
- Sauna: SaunaBench, SaunaBenchHigh, SaunaBenchMid, SaunaBenchLow, SaunaStove.
- Appliances and fireplaces: WashingMachine, Dishwasher, GasStove, IntegratedStove, ElectricalAppliance, Fireplace variants, WoodStove, Chimney.
- Storage: Closet variants, BaseCabinet, WallCabinet.
- Source: [house.py](https://raw.githubusercontent.com/CubiCasa/CubiCasa5k/master/floortrans/loaders/house.py)
- **Shower, Jacuzzi, BaseCabinet, WallCabinet and Misc are dropped from training (mapped to None).** The released model therefore cannot detect showers, even though the SVGs label them. — [house.py](https://raw.githubusercontent.com/CubiCasa/CubiCasa5k/master/floortrans/loaders/house.py)

**Successors that use CubiCasa5k**
- **rbg-research/Floor-Plan-Detection** studies how super-resolution affects detection. It uses CubiCasa5K pretrained weights for walls, icons and rooms. — [GitHub](https://github.com/rbg-research/Floor-Plan-Detection)
- **Raster2Seq** (Cornell, SIGGRAPH 2026, arXiv 2602.09016) outputs rooms, windows and doors as labelled polygon sequences. It claims state-of-the-art results on Structured3D, CubiCasa5K and Raster2Graph, and tests generalization on WAFFLE. The abstract gives no numbers and does not name a code repo; the project page is cornell-vailab.github.io/Raster2Seq. — [arXiv](https://arxiv.org/abs/2602.09016)
- **fpvec-lab** (arXiv 2608.25608, 2026) is a detection-heatmap wall graph compared against autoregressive sequence decoding, evaluated on CubiCasa5K with corrected annotations:
  - Detection beats sequence decoding on walls: +2.7 wall F1 at tolerance 0.05 and +5.1 at tolerance 0.015.
  - Reading an opening heatmap raised opening F1 2.6x without retraining.
  - Fusing the two outputs raised wall F1 by 7 points.
  - Code, the benchmark and corrected CubiCasa annotations are at github.com/Cyprinus12138/fpvec-lab. The abstract does not say whether weights are released.
  - Source: [arXiv 2608.25608](https://arxiv.org/abs/2608.25608)

### Inferences
- For a Finnish-plan hackathon, the fastest high-value move is to **parse the CubiCasa5k SVGs yourself** and convert `FixedFurniture` and `Door`/`Window` polygons into YOLO bounding boxes for the exact classes you need: Toilet, Sink variants, Shower/ShowerCab/ShowerPlatform, Bathtub, SaunaBench and SaunaStove, Door, Window, and Stairs from the `Stairs` groups. Then fine-tune a YOLO detector. This gets around the official model's missing shower and stairs classes.
- The official model's icon IoU is about 55-67% and bathtub IoU only 26.7%. Use it for wall and room segmentation priors, not for reliable counting.
- Because of CC BY-NC-SA, CubiCasa-trained weights are fine for a hackathon or research, but any commercial product would need permission or a re-train on owned data.
- **[prior knowledge, unverified]** CubiCasa5k folders typically contain `F1_original.png`, `F1_scaled.png` and `model.svg` for each sample. Zenodo did not list the archive contents, so check after download.

### Gaps
- The CubiCasa code licence was not named on the GitHub page. Only the dataset licence (CC BY-NC-SA 4.0) was confirmed.
- No per-class door, window or opening F1 numbers were found for Raster2Seq or other 2024-26 successors. Only fpvec-lab's relative gains were found.
- Whether Raster2Seq has released code or weights was not confirmed.

## 2. Newer floor plan recognition repos and models (2022-2026)

### Takeaway
The raster-plan state of the art (Raster-to-Graph, Raster2Seq, RoomFormer/PolyRoom-style polygon transformers) is research-grade, with checkpoints only for some models, and mostly trained on CubiCasa, Structured3D or a Chinese R2G dataset. The highest symbol-spotting numbers (VecFormer at 91.1 PQ, SymPoint, CADTransformer, DPSS) assume vector CAD input, not raster scans. For raster counting in 2-3 days, the practical path is a YOLO model: either a ready-made Hugging Face or Roboflow model, or your own fine-tune on CubiCasa-derived boxes.

### Cited Findings
**Raster to vector / room reconstruction**
- **Raster-to-Graph** (EG 2024, SizheHu) predicts the floor plan as a structural graph using an autoregressive transformer. It ships a dataset of more than 10,000 residential plans. — [GitHub](https://github.com/SizheHu/Raster-to-Graph)
- **neural_floorplan** (daegeun-kim) vendors Raster-to-Graph with a pretrained wall-graph checkpoint (frozen encoder plus a 7-class decoder). This confirms that Raster-to-Graph checkpoints are usable. — [GitHub](https://github.com/daegeun-kim/neural_floorplan)
- **RasterScan/Floor-Plan-Recognition** is an on-premise implementation based on "Raster-to-Vector: Revisiting Floorplan Transformation". It added a room-determination algorithm in August 2024. — [GitHub](https://github.com/RasterScan/Floor-Plan-Recognition)
- **TINY-KE/FloorPlanParser** is a service that returns wall, window and door endpoints as JSON for a POST-ed image. — [GitHub](https://github.com/TINY-KE/FloorPlanParser)
- **floorplan-vectorizer** (Maximilianogc32) is a Claude skill that turns a plan image into an interactive measured SVG with room areas, which is a VLM-driven approach. — [GitHub](https://github.com/Maximilianogc32/floorplan-vectorizer)
- **RoomFormer** (CVPR 2023): code and models are at github.com/ywyue/RoomFormer. It predicts closed room polygons as corner sequences. — [search summary of PolyRoom/RoomFormer papers](https://ar5iv.labs.arxiv.org/html/2407.10439)
- **PolyRoom** (ECCV 2024): code is at github.com/3dv-casia/PolyRoom. It is a room-aware transformer that refines initial room shapes. — [PolyRoom paper](https://ar5iv.labs.arxiv.org/html/2407.10439)
- **FRI-Net** (ECCV 2024) is evaluated on Structured3D and SceneCAD, not CubiCasa. These methods reconstruct plans from 3D point-cloud density maps, not drawings. — [FRI-Net arXiv](https://arxiv.org/pdf/2407.10687)
- **Evidence-gated multimodal parsing and vectorization of architectural floor plans** (arXiv 2609.25615, 2026) appeared in search results but was not read. — [arXiv](https://arxiv.org/pdf/2609.25615)

**Symbol spotting on CAD / vector drawings**
- **CADTransformer** (CVPR 2022) raised panoptic quality (PQ) on FloorPlanCAD from 0.595 to 0.685. Code is at VITA-Group/CADTransformer. — [CVF](https://openaccess.thecvf.com/content/CVPR2022/html/Fan_CADTransformer_Panoptic_Symbol_Spotting_Transformer_for_CAD_Drawings_CVPR_2022_paper.html); [GitHub](https://github.com/VITA-Group/CADTransformer)
- **SymPoint** (ICLR 2024) claims +9.6 PQ and +10.4 RQ absolute on FloorPlanCAD. — [arXiv 2401.10556](https://arxiv.org/pdf/2401.10556v1.pdf)
  - Repo nicehuster/SymPoint: about 61 stars, 7 commits, last news March 2024. Weights are on OneDrive.
  - It takes vector SVG input, parsed with svgpathtools into JSON.
  - Source: [GitHub](https://github.com/nicehuster/SymPoint)
- **VecFormer** (2025) reports 91.1 PQ on FloorPlanCAD. Code is at github.com/WesKwong/VecFormer. — [arXiv 2505.23395](https://arxiv.org/pdf/2505.23395)
- **DPSS** (Dual-Pathway Symbol Spotter) is the ArchCAD-400K baseline. Its code and the dataset were released on 16 October 2025. — [ArchCAD project page](https://archiai-lab.github.io/ArchCAD.github.io)

**Ready-made YOLO detectors**
- **SamirShabani/Architect** (Hugging Face) is a YOLOv8m model fine-tuned on FloorPlanCAD rendered to 640×640 PNGs.
  - It covers 28 classes, including door, window, stairs, sink, bath, bathtub, toilet, squat toilet, urinal and elevator.
  - Reported mAP50 is 0.877 and mAP50-95 is 0.808.
  - Licence: CC BY-NC 4.0 (non-commercial).
  - It loads with one line: `YOLO('SamirShabani/Architect')`.
  - The card's own caveats: doors and windows dominate the data, text is ignored, and performance may drop on noisy or low-resolution scans.
  - Source: [HF model card](https://huggingface.co/SamirShabani/Architect/blob/main/README.md)
- **Roboflow Universe** has many small floor plan projects with hosted APIs or exportable datasets. Class names vary widely, and none reported mAP, dataset size or licence in the search results. Examples:
  - floorplan-ai, with classes door, window, wall, Appliance_Shower and Appliance_Sink — [link](https://universe.roboflow.com/darachs-workspace/floorplan-ai)
  - floorplan-detection-z2q7t — [link](https://universe.roboflow.com/2d-house-plan-object-detection/floorplan-detection-z2q7t)
  - parse/floor-plan-detection, whose sample classes include door, toilet, window, wall and bath tub — [link](https://universe.roboflow.com/parse/floor-plan-detection-ouhua-za5i6)
  - architectural-object-detection (revitai) — [link](https://universe.roboflow.com/revitai/architectural-object-detection-ufmql/dataset/)
  - floorplandetector (intoaec) — [link](https://universe.roboflow.com/intoaec/floorplandetector-l8gle)
  - window-detection-in-floor-plans — [link](https://universe.roboflow.com/bytetrooper/window-detection-in-floor-plans)
  - floorplans-1ouim — [link](https://universe.roboflow.com/floorrecognition/floorplans-1ouim)
  - Source for the class lists: [Roboflow search results](https://universe.roboflow.com/darachs-workspace/floorplan-ai)

### Inferences
- **Hackathon recommendation**
  - (a) Day 1 baseline: zero-shot SamirShabani/Architect, plus one or two Roboflow datasets merged.
  - (b) Fine-tune YOLOv8/YOLO11 on CubiCasa5k SVG-derived boxes for Finnish-specific fixtures such as sauna bench, sauna stove and shower.
  - (c) Use the CubiCasa model or Raster-to-Graph for walls and rooms.
  - Vector-only models (SymPoint, VecFormer, CADTransformer, DPSS) only apply if the inputs are DWG/DXF/PDF vectors, not scans.
- **[prior knowledge, unverified]** Several other options were not checked in this session: their licence, last activity and stars were not looked up.
  - Repos: DeepFloorplan (zlzeng, ICCV 2019, TF1), TF2DeepFloorplan (zcemycl, TF2, with a pip-installable package and pretrained weights), and the original Raster-to-Vector repo (art-programmer/FloorplanTransformation, Torch7/Lua, hard to run).
  - Zero-shot models: Grounding DINO / Florence-2 / OWLv2 zero-shot detection of "toilet"/"door" symbols tends to be weak on line-art symbols without fine-tuning. SAM/SAM2 automatic masks can segment enclosed rooms once walls are thickened or binarized, but SAM produces no semantics.

### Gaps
- No public, confirmed SAM2-based floor plan room segmentation repo, and no Florence-2 or Grounding DINO fine-tune for floor plans, was found or verified in this session.
- Star counts and last-commit dates for Raster-to-Graph, RoomFormer, PolyRoom, VecFormer, DPSS and CADTransformer were not collected.
- Licences for the Roboflow projects were not visible.

## 3. Relevant datasets beyond CubiCasa5k

### Takeaway
For raster symbol detection on European housing plans, CubiCasa5k is the main source and nothing else matches it.
- FloorPlanCAD and ArchCAD-400K are large but come from Chinese commercial CAD drawings and are vector-first. ArchCAD is gated and non-commercial.
- ResPlan (17k plans, CC BY 4.0) and MSD (Swiss) are geometry-only: useful for room and wall topology priors, not for symbol appearance.

### Cited Findings
- **FloorPlanCAD** (ICCV 2021) has more than 10,000 CAD floor plans with panoptic symbol annotations in vector form. The project was shut down in early 2022, and you get the data by email. — [FloorPlanCAD site](https://floorplancad.github.io); [paper](https://arxiv.org/pdf/2105.07147.pdf)
- **ArchCAD-400K** contains 413,062 chunks taken from 5,538 standardized drawings, with DPSS as its baseline. — [arXiv 2503.22346](https://arxiv.org/pdf/2503.22346)
  - The Hugging Face dataset (jackluoluo/ArchCAD) is gated, restricted to non-commercial use, and access requests are reviewed. — [HF](https://huggingface.co/datasets/jackluoluo/ArchCAD)
- **ResPlan** has 17,000 residential plans (16,998 per ResPlan-FP) taken from South Asian real-estate listings.
  - The data is CC BY 4.0 and the code is MIT.
  - It contains only derived geometry (Shapely polygons and NetworkX graphs), with no original images.
  - Split: 13,736 train, 1,632 val and 1,632 test, and 154 test plans have near-duplicates in train.
  - Sources: [ResPlan arXiv](https://arxiv.org/pdf/2508.14006); [GitHub](https://github.com/m-agour/ResPlan); [Kaggle](https://kaggle.com/datasets/resplan/resplan)
- **MSD (Modified Swiss Dwellings)** has 5,300 floor plans covering 18,900 apartments in multi-unit buildings. — [as described in ResPlan paper](https://arxiv.org/html/2508.14006v1)
- **Raster-to-Graph dataset** has more than 10,000 residential plans. — [GitHub](https://github.com/SizheHu/Raster-to-Graph)
- **FPLAN-POLY** has 42 plans converted to vectors. — [FloorPlanCAD paper related work](https://arxiv.org/pdf/2105.07147.pdf)

### Inferences
- **[prior knowledge, unverified]** These datasets were not checked in this session:
  - R2V / LIFULL (Raster-to-Vector, about 870 annotated Japanese plans)
  - RPLAN (80k Chinese layouts, vector, by request, academic only)
  - Structured3D (synthetic 3D with floor plans, academic licence)
  - CVC-FP (122 scanned plans, Spanish, includes older and scanned styles)
  - ROBIN
  - SESYD (synthetic symbols)
  - WAFFLE (about 20k wild, internet-scraped plans of diverse and historic buildings, Cornell). WAFFLE is the closest match for historic or varied scans and was used by Raster2Seq for generalization.

### Gaps
- MSD's licence and download location were not confirmed.
- R2V, RPLAN, CVC-FP and WAFFLE details were not verified in this session.

## 4. OCR for small and rotated text on drawings, and auto-orientation

### Takeaway
PP-OCRv5 (PaddleOCR, Apache-2.0) is the strongest verified option for rotated text in a small model. It reports beating Surya and many VLMs on OmniDocBench, including the 90°-rotated subset. docTR (Apache-2.0) is a permissive alternative. Surya is GPL-3.0, which is a copyleft risk. For short Finnish abbreviations (MH, KPH, PH, WC, S, KHH, PARVEKE) and area strings like "12,5 m²", the more important step is to match the OCR output against a closed vocabulary with regex, not to pick the best general OCR.

### Cited Findings
- **PP-OCRv5** (5M parameters, CVPR 2026 paper arXiv 2603.24373) reports 0.067 on OmniDocBench (lower is better) versus 0.090 for Surya, and 0.012 on the Rotate90 subset. These are vendor-published results. — [arXiv 2603.24373](https://arxiv.org/abs/2603.24373); [paper notes](https://en.papernotes.org/CVPR2026/multimodal_vlm/pp-ocrv5_a_specialized_5m-parameter_model_rivaling_billion-parameter_vision-lang/)
- **Surya** is GPL v3; **docTR** is Apache 2.0, a two-stage detection and recognition pipeline. — [Roboflow docTR vs Surya](https://playground.roboflow.com/models/compare/doctr-vs-surya)
- **OCR-Rotation-Bench** (arXiv 2511.04161) is a benchmark built specifically for rotation robustness. — [arXiv](https://arxiv.org/html/2511.04161v2)
- No head-to-head benchmark on engineering drawings was found. — [search result summary](https://arxiv.org/abs/2603.24373)

### Inferences
- **Suggested pipeline**
  - Run PaddleOCR with document orientation classification plus per-line text-angle classification enabled.
  - Tile large scans with overlap, and upscale small text 2-3x before detection.
  - Normalize the output: `,`/`.` decimals, the `m2`/`m²` unit, uppercase.
  - Match room-type tokens against a Finnish dictionary: MH = makuuhuone (bedroom), OH = olohuone (living room), K/KK/KT = keittiö/keittokomero/keittotila (kitchen), KPH = kylpyhuone (bathroom), PH = pesuhuone (washroom), S = sauna, WC, KHH = kodinhoitohuone (utility room), ET = eteinen (hall), VH = vaatehuone (walk-in closet), VAR = varasto (storage), PARVEKE (balcony), TK = tekninen tila (technical room).
  - Then assign each label to the room polygon that contains its centre.
- **[prior knowledge, unverified]**
  - Tesseract (Apache-2.0) has OSD (orientation and script detection), which is useful for estimating whole-page rotation, but it is weak on sparse, scattered labels.
  - VLMs (Qwen2.5-VL / Qwen3-VL, Florence-2 OCR-with-region, GOT-OCR2, olmOCR) can read labels with spatial reasoning but are slower and may hallucinate. Use them as a fallback or verifier on crops.
  - For whole-plan orientation, a cheap trick is to run OCR at 0/90/180/270 degrees and pick the rotation with the highest mean confidence.

### Gaps
- No verified accuracy numbers exist for any OCR engine on floor-plan text or Finnish abbreviations.
- Licences and accuracy for VLM OCR models (Qwen-VL, Florence-2, GOT-OCR2) were not verified in this session.

## 5. Low-resolution, rotated and historic hand-drawn scans

### Takeaway
No public dataset or pretrained model was found that targets hand-drawn or historic floor plan scans specifically. Robustness has to come from preprocessing (deskew, binarization, super-resolution) and augmentation when fine-tuning on CubiCasa- or FloorPlanCAD-derived data.

### Cited Findings
- Super-resolution before detection has been studied with CubiCasa5K-pretrained models in rbg-research/Floor-Plan-Detection. — [GitHub](https://github.com/rbg-research/Floor-Plan-Detection)
- Hand-drawn floor plan understanding is an old research thread, using subgraph isomorphism and the Hough transform. Searches found no modern dataset for it. — [DFKI paper](https://www-live.dfki.de/fileadmin/user_upload/import/5675_4520a864.pdf)
- The Architect YOLO card warns of degraded performance on noisy or low-resolution scans. — [HF](https://huggingface.co/SamirShabani/Architect/blob/main/README.md)
- The CubiCasa5k paper lists image resolution ranging from 50 to 8000 (units unstated), and includes a "colourful" category of 276 images. This gives some built-in variety in resolution and style. — [paper](https://ar5iv.labs.arxiv.org/html/1904.01920)
- In fpvec-lab, the detection advantage grows with plan size and reverses on small plans, so readout choice depends on resolution. — [arXiv 2608.25608](https://arxiv.org/abs/2608.25608)

### Inferences
- Practical stack, using OpenCV only:
  - Deskew with a Hough-line dominant-angle estimate. Plans are mostly Manhattan, so snap the angle to the nearest 90°.
  - Apply adaptive thresholding or Sauvola binarization.
  - Optionally upscale with Real-ESRGAN.
  - Train with augmentations for blur, JPEG artefacts, rotation, line-width jitter and paper texture.
- **[prior knowledge, unverified]** CVC-FP (scanned) and WAFFLE (internet and historic plans) are the best available test sets for "messy" inputs.

### Gaps
- No hand-drawn floor plan symbol dataset was confirmed.
- No measured accuracy of CubiCasa-trained models on hand-drawn or historic scans was found.
