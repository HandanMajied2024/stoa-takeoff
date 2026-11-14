# VLM / Multimodal LLM Understanding of Floor Plans and Construction Drawings (state as of Nov 2026)

Notes by research sub-agent, 2026-11-13. Each number has an inline source. Model names such as "GPT-6 Astra", "Claude Fable 5.2" and "GPT-5.6 Sol" are given exactly as the cited sources print them. Some results date from late 2025 or early 2026 and cover older models; these are flagged **[dated]**.

## 1. Benchmarks and measured scores (esp. counting)

### Takeaway
Off-the-shelf frontier VLMs read text on drawings well (OCR about 0.95). They are poor at counting symbols such as doors and windows: about 34–55% exact-match on the 2026 AECV-Bench, and 42.9% on dense natural-image counting (CountQA). On full sheets and multi-hop takeoff they reach roughly 50–77% on QA benchmarks, against about 95% for experienced professionals. Quantity takeoff is consistently the weakest category. The newest vendor-run detection benchmark (CaseVBench, Nov 2026) shows the best Nov-2026 frontier models at 79–92% F-style detection on cabinets, countertops and callouts, which is a sign of rapid recent progress. It is vendor-run, so treat it with caution.

### Cited Findings

**AECV-Bench (AECFoundry; arXiv 2601.04819, v1 8 Jan 2026) [dated: covers late-2025 models]**
- The benchmark has two parts. The counting part uses 120 floor plans (from CubiCasa5K, CVC-FP and web sources) with counts of doors, windows, bedrooms and toilets. The QA part has 192 drawing-grounded QA pairs. Counting is scored by exact-match and MAPE, and QA by an LLM judge with human review — [arXiv abstract](https://arxiv.org/abs/2601.04819); [GitHub](https://github.com/AECFoundry/AECV-Bench)
- The abstract says OCR/text-centric QA reaches up to 0.95, spatial reasoning is moderate, and symbol-centric understanding, "especially reliable counting of doors and windows", is often 0.40–0.55 and "remains unsolved" — [arXiv](https://arxiv.org/abs/2601.04819)
- Mean counting accuracy: Gemini 3 Pro 51% (MAPE 16%), GPT-5.2 49%, Claude Opus 4.5 42% (MAPE 24.9%), and GLM-4.6V 39% (best open model). Best per class: bedrooms 91% (GPT-5.2 / Claude Opus 4.5), toilets 82%, doors 39%, windows 34% (both Gemini 3 Pro). Window MAPE sometimes exceeded 60–70% — [AECFoundry blog, upgrade post](https://www.aecfoundry.com/blog/can-ai-really-read-your-building-plans-aecv-bench-gets-a-major-upgrade)
- QA: Gemini 3 Pro scored 0.854 (top) and Grok 4.1 Fast 0.312 (bottom). Category pattern: OCR about 0.95, comparative about 0.80, spatial about 0.70, instance counting about 0.40–0.55 — [AECFoundry blog](https://www.aecfoundry.com/blog/can-ai-really-read-your-building-plans-aecv-bench-gets-a-major-upgrade)
- An earlier version used 150 CubiCasa5k plans and 7 models. Gemini 2.5 Pro led with 41% mean accuracy, and the best MAPE was 18.8% **[dated, 2025]** — [AECFoundry blog v1](https://www.aecfoundry.com/blog/can-ai-really-read-your-building-plans-introducing-aecv-bench)

**DrawingVQA (LSU/UIUC; arXiv 2607.15418, CVPR 2026 Findings) [models are late-2025]**
- 33 "Issued for Construction" structural drawings and 92 expert QA pairs — [arXiv](https://arxiv.org/abs/2607.15418)
- Overall scores: Gemini-3-pro-preview 77.2%, Gemini-2.5-pro 71.7, Gemini-2.5-flash 66.3, Qwen3-VL-32B 58.7, o3 58.7, Claude-4.5-Sonnet 57.6, Claude-4.5-Haiku 54.3, GPT-4o 48.9, random 27.2. Human scores: average 68.4, experienced professionals (3+ yrs) 94.9 — [arXiv HTML](https://arxiv.org/html/2607.15418)
- Quantity Take-Off was the weakest aspect for nearly all models. The top QTO score was Gemini-2.5-pro at 41.7, and several models scored near 0 — [arXiv HTML](https://arxiv.org/html/2607.15418)

**LED-BENCH (Tongji; arXiv 2610.19571, Oct 2026) — large-format engineering drawings (mechanical / architectural / transportation)**
- 107 full-size sheets and 377 questions, 11 models — [COXIT summary](https://coxit.co/blog/ai-benchmarks-for-drawings/); [arXiv](https://arxiv.org/abs/2610.19571)
- Domain average: GPT-5.6 Sol 52.65% (Arch 48.89), GPT-5.6 Luna 47.26, Qwen3.8-Max 46.82, Gemini-3.5 Flash 41.45 (Arch 35.11), GPT-5.5 32.87, Kimi-K2.5 24.79, Qwen3.8-27B 22.36. All models dropped on Hard questions — [arXiv HTML](https://arxiv.org/html/2610.19571)

**CaseVBench (COXIT, vendor-run; v7 13 Nov 2026) — object detection/counting on architectural sheets**
- 119–120 pages from 9 sets with 1,430 expert-boxed objects (cabinets, countertops, floor plans, elevations, callouts). A box counts at IoU ≥ 0.50 — [COXIT benchmark page](https://coxit.co/ai-drawing-benchmark/)
- Overall: GPT-6 Astra 92%, Claude Fable 5.2 85%, Gemini 4 Carbon 83%, Claude Opus 5.5 79%, Gemini 4 Argon 76%, Gemini 3.8 Flash 70%, GPT-5.6 Sol 65%, Qwen3.8-Max 62%. The lowest scorers were DeepSeek V4.1 Flash 16%, Grok 4.7 20% and Claude Sonnet 5 21%. Countertops were the weakest category — [COXIT](https://coxit.co/ai-drawing-benchmark/)
- Caveat: COXIT sells takeoff systems and the scores are self-reported. The page says "20 models" in one place but compares 24 — [COXIT](https://coxit.co/ai-drawing-benchmark/)

**Takeoff-level benchmarks**
- Handoff "Construction Blueprint Takeoff Benchmark" (arXiv 2608.15032) uses 10 residential sets with 2,009 verified line items, scored on coverage and Precision@25%. Seven frontier/open models scored 35–61 composite. Professional estimators scored 77.6. Handoff-H1 (CV models plus tool-using agents plus a knowledge base) scored 81.6 — [arXiv](https://arxiv.org/abs/2608.15032). COXIT's summary names Claude Fable 5 at 61.4 as the best general model — [COXIT blog](https://coxit.co/blog/ai-benchmarks-for-drawings/)
- Togal "Construction's Last Exam" has 33 takeoff tasks, on which frontier models scored 2–34%. This is not independently verified, and my search could not find the primary page — [COXIT blog](https://coxit.co/blog/ai-benchmarks-for-drawings/)
- Nomic AEC-Bench has 196 agent tasks across drawings, specs and submittals (arXiv 2603.29199). No numbers were retrieved — [COXIT blog](https://coxit.co/blog/ai-benchmarks-for-drawings/)

**Area estimation / floor plan spatial QA**
- Zero-shot room-area estimation (Periodica Polytechnica, 2026) used 100 plans and 472 comparisons with 3 open VLMs. The VLMs reached R² ≈ 0.71 and MAPE ≈ 43%, with larger errors on small rooms. A classical colour-segmentation pixel count reached MAPE 5.68% per room and 1.58% per plan — [pp.bme.hu](https://pp.bme.hu/ci/article/view/44138)
- FloorplanQA (ICML 2026; arXiv 2507.07644) has 2,000 *symbolic* layouts and 16,000 QA pairs across 8 task types, including free floor area computed with Shapely. It evaluates 15 LLMs. It tests text-only spatial reasoning, not pixels — [arXiv](https://arxiv.org/pdf/2507.07644)
- Blueprint-Bench 2 (Andon Labs) asks models to build a floor plan from about 20 photos. Gemini 4 Argon scored 0.544 against a human 0.586 — [COXIT blog](https://coxit.co/blog/ai-benchmarks-for-drawings/)

**Mechanical / symbol benchmarks**
- MechVQA (arXiv 2605.30794) has 3.3K mechanical drawings and 21K QA pairs over 10 subtasks — [arXiv](https://arxiv.org/html/2605.30794v2)
- BlueprintSymVL (Chalmers, 2025) tested GPT-4o, Gemini 2.5 Pro, InternVL2.5-78B and Qwen2.5-VL-72B on blueprint symbol recognition. It found notable degradation in cluttered views **[dated]** — [Chalmers](https://research.chalmers.se/en/publication/549362)

**General counting**
- CountQA (Google/Waymo, Aug 2025) has more than 1,500 dense, cluttered real images and tests 15 MLLMs. The best scored 42.9%, and accuracy fell as counts rose **[dated]** — [arXiv 2508.06585](https://arxiv.org/abs/2508.06585)
- Qwen2.5-VL-72B scored 93.6 on CountBench, a sparse general benchmark, which shows how much easier sparse counting is than drawing counting **[dated, Feb 2025]** — [Qwen2.5-VL tech report](https://arxiv.org/pdf/2502.13923)

### Inferences
- Benchmarks disagree a lot because the tasks differ: whole-plan exact counts (AECV, about 40–50%), IoU detection on page crops (CaseVBench, up to 92%) and multi-sheet reasoning (LED, DrawingVQA, about 50–77%). The best Nov-2026 models are probably much better than the late-2025 AECV numbers, but no independent re-run of AECV on Nov-2026 models was found.
- Exact-match counting of small repeated symbols on a whole sheet is still the least reliable task. Per-plan totals of large items (rooms, bedrooms) are much better.

### Gaps
- No public per-model AECV-Bench table for the newest (Nov 2026) models was found.
- I could not find benchmarks named "IFC-Bench (drawings)", "BlueprintQA", "CAD-VQA", "ArchCAD QA" or "DrawingQA" as specified. WAFFLE (arXiv 2412.00955, floorplans in the wild) exists, but I did not retrieve its numbers.
- Togal's "Construction's Last Exam" primary source was not found.

## 2. Failure modes

### Takeaway
The main failures are downscaling, which destroys small symbols before inference; confusion between similar symbols; hallucinated or duplicate instances in dense areas; misreading conventions; incomplete cross-sheet search; and relational reasoning errors. Raw text reading is rarely the bottleneck.

### Cited Findings
- AECV-Bench lists these failures: door swing arcs confused with other curves, and doors without arcs missed; glazed doors, curtain walls and skylights miscounted as windows; hallucinated fixtures in dense areas; missed instances where symbols overlap or are crowded; and double doors counted inconsistently (per opening vs per leaf) — [AECFoundry blog](https://www.aecfoundry.com/blog/can-ai-really-read-your-building-plans-aecv-bench-gets-a-major-upgrade)
- CaseVBench lists missed tall cabinets and countertops, loose or offset boxes, split or duplicate boxes, and merged adjacent units. It also notes that much miscounting "starts before inference, when the drawing is compressed to fit the model's input size" — [COXIT](https://coxit.co/ai-drawing-benchmark/)
- DrawingVQA found visual grounding failures: the reasoning plan is sound, but the model loses track when tracing lines or picks the wrong callout. Models also stop after the first plausible cross-reference and lack domain knowledge of weld and structural symbols and acronyms — [arXiv HTML](https://arxiv.org/html/2607.15418)
- LED-BENCH error breakdown: relation reconstruction 47.3%, integrated engineering reasoning 23.4%, object association 17.2%, local evidence reading only 12.1% — [arXiv HTML](https://arxiv.org/html/2610.19571)
- Anthropic's own docs on limitations: Claude "might hallucinate or make mistakes when interpreting low-quality, rotated, or very small images". Counts are "approximate… especially with large numbers of small objects". Coordinates are approximate — [Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)
- Resolution caps: Claude 4.7+ models allow a max long edge of 2,576 px (4,784 visual tokens). Other models allow 1,568 px. Larger images are downscaled silently unless `oversized_image: "error"` is set. Above 20 images per request, each image must be at most 3,000 px per side — [Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision). For comparison, DrawingVQA's default full sheet at 100 PPI is about 4800×3600 px — [arXiv HTML](https://arxiv.org/html/2607.15418)
- Scale/area: VLM room-area MAPE is about 43%, worse for small rooms — [pp.bme.hu](https://pp.bme.hu/ci/article/view/44138). Togal's AI takeoff showed consistent underestimation on area quantities and lower reliability on irregular geometry and façades (independent 2026 case study) — [EasyChair paper](https://easychair.org/publications/paper/pkrRp)

### Inferences
- A full ARCH-D sheet sent whole to any API VLM gets downscaled to about 2.5k px or less. Door swings and window symbols then shrink to a few pixels, which explains much of the counting error. This matches the large gains from crops in Section 3.

### Gaps
- I found no quantitative study isolating the effect of rotated text on drawing OCR.

## 3. Techniques that improve accuracy

### Takeaway
The best-evidenced gains come from more pixels per symbol: overlapping tiles or crops, or search-then-reread, worth about +13 points on LED-BENCH. Further gains come from hybrid pipelines in which dedicated CV detectors do the counting and geometry while the LLM orchestrates and reasons, as in Handoff-H1 (81.6 vs 35–61 for frontier models) and in deterministic pixel or vector measurement for areas (MAPE about 1.6–5.7% vs about 43%). Agentic zoom is not uniformly positive. Published evidence for fine-tuned Qwen/Florence on drawing *counting* is thin.

### Cited Findings
- **Tiling / crops (LED-BENCH, four-model subset, 3 runs)**: whole-sheet 36.38 → fixed overlapping crops 49.34 (+12.96, 1 call) → search-then-reread 49.74 (+13.35, 3 calls). Locate-then-reread gave only +5.05 and *lowered* Mechanical accuracy from 44.12 to 36.47 — [arXiv HTML](https://arxiv.org/html/2610.19571)
- **Resolution**: DrawingVQA accuracy rises with PPI and plateaus beyond 100 PPI. The average was 50.8% at 25 PPI, 53.9% at 75, 55.7% at 100 and 55.3% at 125 — [arXiv HTML](https://arxiv.org/html/2607.15418). LED-BENCH also found that higher rasterisation generally helps — [arXiv HTML](https://arxiv.org/html/2610.19571)
- **Semantic-aware tiling**: blind tiling can cut entities apart. One proposal detects information-dense ROIs first, so crops keep logical boundaries and context — [arXiv 2607.18997](https://arxiv.org/pdf/2607.18997)
- **Tiling + NMS for detectors**: YOLO on tiled floor plans with NMS to remove duplicates across tiles, plus a vector/pixel hybrid symbol spotting method — [Rezvanifar et al., CVPRW 2020](https://openaccess.thecvf.com/content_CVPRW_2020/papers/w34/Rezvanifar_Symbol_Spotting_on_Digital_Architectural_Floor_Plans_Using_a_Deep_CVPRW_2020_paper.pdf) **[dated but foundational]**
- **Detector + LLM hybrid**: Handoff-H1 combines purpose-built CV models for primitives, tool-using agents with CV-backed counting, detection and plan decomposition, and a construction knowledge base. It scored 81.6 vs 77.6 for human estimators and about 20 points above the best frontier agent — [arXiv 2608.15032](https://arxiv.org/abs/2608.15032). Another 2026 paper pairs YOLOv8 symbol detection with segmentation and an LLM for area estimation and compliance — [Applied Sciences 2026](https://doi.org/10.3390/app16136290)
- **Deterministic measurement beats VLM estimation**: pixel counting gave MAPE 5.68% per room, 1.58% per plan, vs about 43% for VLMs — [pp.bme.hu](https://pp.bme.hu/ci/article/view/44138)
- **"Thinking with images" / zoom**: DeepEyes (RL-trained zoom, 7B) scored 90.1% on V*, +18.9 over Qwen2.5-VL-7B, with +6.3 and +7.3 on HR-Bench 4K and 8K — [arXiv 2505.14362](https://arxiv.org/pdf/2505.14362v3). ZoomEye's training-free tree search added +34.57 on V* for LLaVA-1.5-7B — [arXiv 2411.16044](https://arxiv.org/pdf/2411.16044). These are natural-image results, not drawings **[2025]**
- **Points/boxes grounding**: Claude returns absolute pixel coordinates in the *resized* image, so coordinates must be rescaled, or images pre-resized, to map back to the original — [Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision). CaseVBench shows box quality varies widely by model (16–92%) — [COXIT](https://coxit.co/ai-drawing-benchmark/)
- **Fine-tuning**: FloorplanVLM (arXiv 2602.06507) applies LoRA SFT plus GRPO to Qwen2.5-VL-3B on CubiCasa5K, targeting SVG-derived JSON (walls, rooms, openings). It is a vectorisation task — [HF model card](https://huggingface.co/mudasir13cs/qwen25-vl-3b-floorplan-sft). A crowd-counting recipe applies LoRA rank 64 to Qwen2.5-VL-7B and also adapts the vision tower — [arXiv 2609.23012](https://arxiv.org/pdf/2609.23012)

### Inferences
- A practical recipe consistent with the evidence:
  1. Rasterise at about 100–150 PPI.
  2. Tile with overlap, or find ROIs first, so each tile stays within the model's native resolution (2,576 px for Claude 4.7+).
  3. Have the VLM return points or boxes per symbol rather than a bare number.
  4. De-duplicate across tiles with NMS.
  5. Compute counts, lengths and areas in code using scale from dimension strings or the title block.
  6. Cross-check with a second independent method, such as a detector count vs a VLM count, or a vector/PDF text extraction vs vision. Flag disagreements for human review.
- Self-consistency (majority vote over N samples) is plausible but untested here: I found no drawing-specific study quantifying it, and its cost scales linearly with N.

### Gaps
- No drawing-specific evaluation of set-of-mark prompting, self-consistency, or Florence-2 fine-tuning for symbol counting was found.
- No published results were found for fine-tuned Qwen2.5-VL on floor-plan symbol *counts*.

## 4. Cost and latency for ~10k images

### Takeaway
At Nov-2026 prices, one full-resolution pass over 10k drawing images costs tens to low hundreds of USD in input tokens. CaseVBench measures $0.004–$0.19 per page and 5–155 s per page for frontier models. Tiling multiplies token cost by roughly the tile count, and batch APIs halve it.

### Cited Findings
- Claude image tokens are ⌈w/28⌉×⌈h/28⌉, capped at 4,784 tokens (2,576 px long edge) on Claude 4.7+. A 1000×1000 image is 1,296 tokens. At Opus 5.5's $4 per million input tokens, a 1 MP image costs about $5.18 per 1,000 images and a 4K image about $19.14 per 1,000. Haiku 4.5 at $1 per million costs about $1.30 per 1,000 for 1 MP — [Claude vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)
- CaseVBench median cost and time per page: GPT-6 Astra $0.186 / 28.2 s; Claude Fable 5.2 $0.079 / 8.8 s; Claude Opus 5.5 $0.040 / 8.9 s; Gemini 4 Argon $0.021 / 9.8 s; Qwen3.8-Max $0.055 / 154.9 s. The cheapest was GPT-6 Luna at $0.004 per page. A 200-sheet set costs $37 on GPT-6 Astra and $16 on Claude Fable 5.2 — [COXIT](https://coxit.co/ai-drawing-benchmark/)
- Batch APIs at Anthropic, OpenAI and Google all give a 50% discount, and Claude batches accept image inputs — [Anthropic batch docs](https://platform.claude.com/en/docs/build-with-claude/batch-processing); [Anthropic announcement](https://anthropic.com/news/message-batches-api)
- LED-BENCH's search-then-reread uses 3 model calls vs 1 for fixed crops, for about the same accuracy — [arXiv HTML](https://arxiv.org/html/2610.19571)

### Inferences
- Rough estimates of my own (input tokens only): 10k images × 4,784 tokens on Opus 5.5 is about $190 single-pass, or about $95 batched. With 9 tiles of about 1,500 tokens each, it is about $540, or about $270 batched. Output and reasoning tokens come on top. Scaling CaseVBench per-page medians to 10k pages gives about $40 (GPT-6 Luna) to $1,860 (GPT-6 Astra). Latency is irrelevant under batch processing (24 h SLA). Synchronous runs need concurrency, since 9–155 s per page × 10k pages is about 1–18 days serial.
- Fixed overlapping crops are the cost-efficient default (1 call, gains similar to agentic search).

### Gaps
- Exact output-token pricing for each model was not gathered. Current batch size limits differ by source.

## 5. LLM agents for quantity takeoff and BIM/IFC QA

### Takeaway
On IFC/BIM data, the proven pattern is LLM planning plus deterministic query tools, using agentic, iterative exploration rather than one-shot query generation. It reaches about 80% on IFC-Bench v1. The quality of the BIM model matters more than the strength of the LLM. For drawings, end-to-end takeoff agents built on frontier models alone remain well below estimators. Hybrid CV-plus-agent systems now match or beat estimators on one benchmark.

### Cited Findings
- IFC-Bench v1 (Hellin et al., EC3 2025): a multi-agent natural-language IFC retrieval workflow reached 80% overall accuracy across architectural, structural and MEP domains, with an open dataset — [EC3 2025](https://ec-3.org/publication/ec32025_265/)
- ifc-bench v2 / "BIM Information Extraction Through LLM-based Adaptive Exploration" (arXiv 2605.01698, May 2026): 1,027 QA pairs over 37 IFC models from 21 projects. "Agentic search", in which the LLM iteratively queries the model, significantly outperforms static query generation in a factorial ablation. BIM model quality matters more than the LLM backbone — [arXiv](https://arxiv.org/pdf/2605.01698)
- IFCMemoryBench (KDD 2026 workshop): 143 multi-session tasks with accuracy still below 60% — [search summary, unverified](https://de.linkedin.com/in/amirojalvo)
- Constrained text-to-graph querying with IDS gave better execution accuracy, with competitive small open-weight models (EC3 2026) — [EC3 2026](https://ec-3.org/wp-content/uploads/2026/08/EC32026_347.pdf). LLM-as-judge for BIM-QA was tested on 74 IFC-Bench pairs. The authors argue binary accuracy misses quality aspects such as disclosure of the calculation method — [TUM](https://mediatum.ub.tum.de/doc/1858932/1858932.pdf)
- An MCP-server reference architecture for agentic BIM describes the common pattern: the LLM plans and orchestrates local API tools, with lightweight iterative checking — [arXiv 2601.00809](https://arxiv.org/pdf/2601.00809)
- Open-source ifc-agent-tools exposes deterministic quantity takeoff (deducting openings from wall volumes) as an MCP server and Claude Code skill. The LLM only chooses tools and interprets results — [GitHub](https://github.com/masoodkaramoozian/ifc-agent-tools)
- For drawings: Handoff-H1 scored 81.6 vs 77.6 for estimators and 35–61 for frontier models — [arXiv 2608.15032](https://arxiv.org/abs/2608.15032). DrawingVQA QTO was at most 41.7 — [arXiv HTML](https://arxiv.org/html/2607.15418)

### Inferences
- The architecture that transfers best to drawing takeoff mirrors the IFC work. Turn drawings into structured, queryable data (detections, OCR'd dimensions, vector geometry), then let the LLM answer questions by querying that data with tools and computing in code. Avoid answering from pixels in one shot.

### Gaps
- Most IFC accuracy numbers come from abstracts and summaries, not full papers. The benchmarks are not comparable to each other.
