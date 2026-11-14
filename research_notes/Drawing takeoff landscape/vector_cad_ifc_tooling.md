# Open-source tooling for vector construction drawings and BIM (PDF / DXF / DWG / SVG / IFC, plan-to-3D, web viewers, LLM-over-BIM)

Scope: a catalogue for a pipeline of parse drawings -> structured building model (rooms, doors, windows, fixtures as polygons) -> quantities -> 2D/3D web and mobile viewer. Researched 2026-11-13.

Verification note: this session made 16 web searches. Items tagged **[PK]** come from prior knowledge plus the project's canonical URL and were NOT re-checked in this session. Treat them as likely correct but confirm the LICENSE file and latest release before you rely on them. Untagged items have the source cited inline. Much of the confirmation came from search-result summaries, package indexes (PyPI, npm, jsDelivr), mirrors and directories rather than primary LICENSE files. Where that matters, it is flagged.

---

## 1. PDF vector extraction (PyMuPDF, pdfplumber, pdf.js, vector paths, schedule tables, scale detection)

### Takeaway
PyMuPDF (`Page.get_drawings()`) is the most capable Python vector-path extractor, but it is AGPL or paid commercial (Artifex). That is the biggest licensing decision in the pipeline. pdfplumber/pdfminer.six (MIT) and pdf.js (Apache-2.0) are the permissive alternatives. No library detects scale off the shelf, so title-block and scale-bar parsing has to be custom code.

### Cited Findings
- **PyMuPDF** (https://github.com/pymupdf/PyMuPDF, Python bindings over MuPDF in C). `Page.get_drawings()` turns a page's draw commands into a list of Python dicts covering lines, curves, rectangles, fill and stroke colours, widths and dashes. It was added in v1.18.0. — [PyMuPDF docs: Drawing and Graphics](https://pymupdf.readthedocs.io/en/latest/recipes-drawing-and-graphics.html)
  - Pitfall: `get_drawings()` "will always return all paths" and ignores instructions that hide areas of a page. Clipped or hidden geometry (e.g. viewport-clipped xrefs in CAD-exported PDFs) comes back as well, so you must apply clipping yourself (`get_drawings(extended=True)` exposes clip and group info [PK]). — [PyMuPDF docs](https://pymupdf.readthedocs.io/en/latest/recipes-drawing-and-graphics.html)
  - Licence: AGPL-3.0 or an Artifex commercial licence. Artifex is the exclusive commercial licensing agent for MuPDF. The docs send anyone who cannot meet the AGPL to Artifex. — [PyMuPDF about / features comparison](https://pymupdf.readthedocs.io/en/latest/about.html); [Artifex blog on vector extraction](https://artifex.com/blog/extracting-and-creating-vector-graphics-in-a-pdf-using-python-pymupdf)
  - A competing vendor calls AGPL "a non-starter" for closed-source and SaaS backends. That is vendor marketing, but the underlying point holds: AGPL section 13 reaches network use. — [pdfspine docs](https://pdfspine-docs.pages.dev/docs)
  - PyMuPDF also has table extraction (`page.find_tables()`) and the companion pymupdf4llm [PK].
  - There is a public PyMuPDF GitHub discussion (#4883) titled "Vector-first quantity takeoff: extracting accurate measurements from vector PDFs / IFC". It shows practitioners are already attempting this exact pipeline. — [PyMuPDF discussion mirror](https://gh.r-mj.com/pymupdf/PyMuPDF/discussions/4883)
- **pdfplumber** (https://github.com/jsvine/pdfplumber, MIT, Python, built on pdfminer.six) [PK]. It exposes `page.lines`, `page.rects`, `page.curves`, chars with coordinates, and a table finder you can tune with explicit line strategies. That suits ruled door, window and finish schedules. Pitfalls: much slower than MuPDF on dense CAD sheets with 100k+ path segments. Curves become point lists. Text in CAD PDFs is often exploded into per-glyph paths or SHX "text as geometry", which leaves no extractable text at all.
- **pdf.js** (https://github.com/mozilla/pdf.js, Apache-2.0, JS) [PK]. It renders in the browser and has an operator list API (`page.getOperatorList()`) for raw path ops, but no high-level "drawings" API. It is a good choice for the 2D web viewer and overlay layer, and a poor one for server-side extraction.
- Other permissive or alternative options [PK]: **pypdfium2** (Apache-2.0/BSD, PDFium bindings, page objects including paths); **pikepdf** (MPL-2.0, low-level content-stream parsing via qpdf); **Camelot** (MIT) and **tabula-py** (MIT, Java) for lattice tables; **Poppler pdftocairo -svg** (GPL) to convert PDF to SVG and then parse paths with **svgpathtools** (MIT) / **svgelements** (MIT).
- **Scale detection**: no maintained open-source library for scale detection on drawings turned up in this session. See Gaps.

### Inferences
- If the product is a closed-source SaaS, either buy a MuPDF commercial licence or build the extractor on pypdfium2 or pdfminer/pdfplumber. Don't ship PyMuPDF under AGPL without your legal team's approval.
- Vector-first beats raster ML on CAD-exported PDFs. Wall hatches, door swing arcs (curves of fixed radius at a wall gap) and closed room-boundary polylines can all be read straight from the paths. Scanned PDFs still need raster CV.
- Schedules (door, finish, window) are usually ruled tables. Line-based table detection from pdfplumber or PyMuPDF `find_tables` works when real text is present. Where text has been converted to outlines, you need OCR on a rendered crop.
- For scale, a practical approach is to (a) regex title-block text for `1:50`, `1/4" = 1'-0"`, `SCALE`; (b) find scale-bar candidates (alternating filled rects with numeric labels); (c) cross-check against a known dimension string such as a door width of about 900 mm. Per-viewport scales on one sheet are common, so attach the scale to a viewport region, not to the page.

### Gaps
- No open-source scale-bar or title-block scale detector was verified. Published academic work may exist, but none was found in this session.
- Did not verify whether PyMuPDF's licence or pricing changed in 2026.

---

## 2. DXF / DWG (ezdxf, LibreDWG, ODA File Converter, symbol counting)

### Takeaway
ezdxf (MIT) is the default for DXF read/write, layer and block queries, and bounding boxes. DWG is the legal and technical pain point. LibreDWG is GPL-3 (it can read all DWG versions since 0.13). The ODA File Converter is free proprietary freeware, and its licence terms for server or commercial batch use were not confirmed.

### Cited Findings
- **ezdxf** (https://github.com/mozman/ezdxf, Python, MIT): "licensed under the very liberal MIT-License". — [ezdxf introduction](https://ezdxf.readthedocs.io/en/stable/introduction.html)
  - Layer and block queries use selector syntax, e.g. `msp.query('LINE[layer=="MyLayer"]')` and `msp.query('INSERT[name=="FLAG"]')` to find all references to a block. — [ezdxf blocks tutorial (Debian source)](https://sources.debian.org/src/ezdxf/1.4.1-1/docs/source/tutorials/blocks.rst)
  - `ezdxf.bbox.extents(entities, fast=False)` returns combined bounding boxes. For INSERTs it uses the sub-entities. — [ezdxf bbox docs](https://ezdxf.readthedocs.io/en/stable/bbox.html)
  - Debian packages version 1.4.x (1.4.1, 1.4.3), so the project is actively maintained. — [Debian sources](https://sources.debian.org/src/ezdxf/1.4.3-1/docs/source/bbox.rst)
  - [PK] It also ships `ezdxf.addons.odafc` (a wrapper that calls the ODA File Converter for DWG I/O), `ezdxf.addons.drawing` (render to SVG, PDF or matplotlib), `ezdxf.addons.geo` (`__geo_interface__` / shapely bridging) and `ezdxf.disassemble` / `explode` for nested blocks.
- **Symbol counting** (inference supported by the docs above): count = `len(msp.query('INSERT[name=="DOOR_*"]'))`. You need to handle nested INSERTs (blocks in blocks), dynamic blocks (anonymous `*U###` names, where you resolve the original via the XDATA/extension dict [PK]), MINSERT arrays, and inserts in paper-space vs model-space.
- **LibreDWG** (https://www.gnu.org/software/libredwg/, https://github.com/LibreDWG/libredwg, C, GPL-3.0): since 0.13 (Feb 2024) it reads all existing DWG versions. 0.13.3 is a bugfix release. Its `dwg2dxf` tool writes ASCII or binary DXF; the openSUSE man page lists r12 to r2013 as output versions. — [Wikipedia](https://en.wikipedia.org/wiki/LibreDWG); [GitHub release 0.13.3](https://www.github.com/LibreDWG/libredwg/releases/tag/0.13.3); [dwg2dxf man page](https://manpages.opensuse.org/Leap-16.0/libredwg-tools/dwg2dxf.1.en.html)
  - Licence pitfall: GPL-3. Assimp's maintainer said the GPL rules it out for Assimp and many other applications. — [Wikipedia](https://en.wikipedia.org/wiki/LibreDWG)
  - Version conflict: one Wikipedia mirror lists 0.14 (27 June 2026) as the stable release, while others list 0.13.3. Not resolved. — [mirror](https://wiki.krisyotam.com/content/wikipedia_en_all_nopic_2026-03/LibreDWG)
  - Running it as a separate CLI process (`dwg2dxf`) instead of linking to it is the usual way to keep GPL obligations at arm's length [inference, not legal advice]. Write-back fidelity and complex entities (proxy objects, some AEC objects) are known weak spots [PK].
- **ODA File Converter** (https://www.opendesign.com/guestfiles/oda_file_converter): free, cross-platform (Windows, Mac, Linux) DWG<->DXF converter with folder batch conversion. — [third-party review](https://get.nero.com/publishers/ODA/ODAFileConverter%5CODAFileConverter.html). AlternativeTo classifies its predecessor, Teigha File Converter, as "Proprietary / Free product". — [AlternativeTo](https://alternativeto.net/software/teigha-file-converter/about/)
  - Pitfall: proprietary freeware. The EULA was not found in this session, so use in a commercial SaaS backend is unconfirmed. On Linux it needs a GUI/Qt runtime (headless servers usually use xvfb) [PK].
- Other options [PK]: **LibreCAD's libdxfrw** (GPL-2, C++, reads DWG R14 to 2018 in part); **Open CASCADE / FreeCAD** (LGPL) can import DXF; **dxf-parser** (MIT, JS) for parsing DXF in the browser; **three-dxf** / **dxf-viewer** (vagran/dxf-viewer, MPL-2.0) for WebGL DXF rendering.

### Inferences
- Recommended route: DWG -> (ODA File Converter if its EULA allows, else a sandboxed LibreDWG `dwg2dxf` process) -> ezdxf -> shapely. Keep DWG conversion in an isolated worker.
- In CAD sources, layer naming conventions (AIA/NCS `A-DOOR`, `A-WALL`, `A-FLOR-*`; ISO 13567) and block names are the cheapest classification signals, far more reliable than geometry heuristics. They vary by firm, so you need a configurable mapping table.

### Gaps
- The ODA File Converter's current EULA terms for commercial or automated use were not verified.
- The LibreDWG 0.14 release status was not resolved.

---

## 3. IFC (IfcOpenShell, Bonsai QTO, xBIM, web-ifc / That Open, IFC -> glTF/xeokit, Speckle)

### Takeaway
IfcOpenShell (LGPL-3.0-or-later; current 0.8.x) is the core for parsing, authoring, geometry and QTO. Its `ifc5d` / `util.shape` quantity engine is usable but still under active fixing, so you need to validate computed quantities. For the web, That Open's `@thatopen/components` / `fragments` 3.x are MIT (web-ifc itself is MPL-2.0). xeokit is AGPL-3 with commercial options. Speckle is mostly Apache-2.0, with enterprise-licensed server modules.

### Cited Findings
- **IfcOpenShell** (https://github.com/IfcOpenShell/IfcOpenShell, C++ core + Python, https://docs.ifcopenshell.org): PyPI has 0.8.0, 0.8.1, 0.8.1.post1 and 0.8.3. Tools including ifcpatch and ifctester are LGPL-3.0-or-later. IfcConvert exports geometry to formats including GLB. Recent commits add `--fail-on-error`. — [PyPI ifcopenshell](https://pypi.org/project/ifcopenshell/0.8.3/); [anaconda](https://anaconda.org/freecad/ifcopenshell)
  - **ifctester**: library, CLI and web app for IDS (Information Delivery Specification) audits. **ifcpatch**: packaged recipes that modify IFC files. — [PyPI](https://pypi.org/project/ifcopenshell)
  - Bonsai (formerly BlenderBIM) tags such as `bonsai-0.8.6-alpha...` (mid-2026) show active development. — [repo mirror tags](https://dev.glassvision.dedyn.io/Glassvision/IfcOpenShell/src/tag/bonsai-0.8.6-alpha2607231751)
  - [PK] Useful utils: `ifcopenshell.util.element` (get_psets, get_type, get_container, get_decomposition), `util.selector` (query syntax such as `IfcDoor, /Pset_.*Common/.FireRating=...`), `util.unit` (unit scaling: always apply `calculate_unit_scale`), `util.placement`, `util.shape` (areas, volumes, footprints), `ifcopenshell.geom` (iterator, multi-threaded tessellation), and `ifcopenshell.api` (high-level authoring: root.create_entity, geometry.add_wall_representation, spatial.assign_container, etc.).
- **QTO engine (ifc5d + util.shape) and its pitfalls**:
  - Bonsai has two calculators: one on the Blender side (`bonsai/bim/module/qto/calculator.py`) and ifc5d using `ifcopenshell.util.shape`. They diverged for some elements (e.g. IfcCovering picking different faces and axes) until fixed (#6728). — [commit](https://dev.glassvision.dedyn.io/Glassvision/IfcOpenShell/src/branch/fix-6728-covering-qto-mismatch); [OSArch discussion: IfcOpenShell vs Bonsai QTO engine](https://community.osarch.org/discussion/comment/22319/)
  - IfcSpace quantities (e.g. GrossFloorArea = `get_footprint_area`) were only wired into ifc5d recently (fix #8570). — [repo tag/commit](https://dev.glassvision.dedyn.io/Glassvision/IfcOpenShell/src/tag/bonsai-0.8.6-alpha2607231751)
  - `util.shape.get_volume` sums signed tetrahedra and is valid only for closed, watertight meshes. It now returns NaN for non-manifold meshes instead of a wrong number. — [commit](https://dev.glassvision.dedyn.io/Glassvision/IfcOpenShell/src/commit/de40b5f685379bf93de8071f7d9a811522db05c9)
  - A community gist (Dion Moult) shows wall `get_side_area` / `get_footprint_area` on `geom.create_shape` output, written into Qto psets. — [gist](https://gist.github.com/Moult/d25e4fe1c295d5fdafe1c3b2f1adeab1)
  - **Stored vs computed quantities**: Qto_* property sets in an IFC are whatever the authoring tool exported. They may be missing, stale after edits, use different net/gross rules (opening deductions, thresholds), or follow a different unit scale. Computing from geometry depends on tessellation quality and watertightness (above). Best practice: compute, compare against stored values, and flag differences. Also check `IfcRelVoidsElement` openings for net areas [inference + PK].
- **xBIM** (https://github.com/xBimTeam, C#/.NET) [PK]: Xbim.Essentials (parse/write IFC2x3/IFC4/IFC4x3) and Xbim.Geometry (OCC-based). Licence is CDDL-1.0 (weak copyleft at file level, commercial-friendly). Good if the backend is .NET.
- **That Open Company (formerly IFC.js)**:
  - **web-ifc** (https://github.com/ThatOpen/engine_web-ifc, C++ -> WASM + TS): repo licence MPL-2.0 per directory listings. The "MIT" claims on third-party skill pages conflict with this. Last push seen 2026-05-12; npm 0.0.7x. — [ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2FThatOpen%2Fengine_web-ifc); [GitHub](https://github.com/ThatOpen/engine_web-ifc); [web-ifc README 0.0.78](https://cdn.jsdelivr.net/npm/web-ifc@0.0.78/README.md)
  - **@thatopen/fragments** (3.4.x on npm, MIT): the docs call it completely free and open source, usable commercially. Fragments is the optimized binary format the viewer streams instead of raw IFC. — [Fragments docs](https://docs.thatopen.com/fragments/getting-started); [npm package.json 3.4.3](https://cdn.jsdelivr.net/npm/@thatopen/fragments@3.4.3/package.json)
  - **@thatopen/components** 3.x: MIT according to a third-party summary. The older openbim-components v1 and IFC.js v0.x were AGPL-3.0. Pin versions and check the LICENSE. — [skills page](https://skillselion.com/skills/openaec-foundation/thatopen-claude-skill-package/thatopen-core-architecture); [docs](https://docs.thatopen.com/Tutorials/Components)
  - Pitfall: web-ifc is still 0.0.x, so expect API churn between versions. The legacy `web-ifc-viewer` / `web-ifc-three` packages are deprecated [PK].
- **xeokit** (https://github.com/xeokit/xeokit-sdk, JS/WebGL): AGPL-3.0, plus custom proprietary licences for enterprise. Current terms say licence terms vary by version, package and channel. — [xeokit.io](https://xeokit.io:); [xeokit terms](https://xeokit.io/terms-of-use); [OSArch thread on licence history](https://community-test.osarch.org/thread/289/p2)
  - IFC -> XKT: the fastest route uses Creoox's closed-source `ifc2gltfcxconverter` plus open-source `convert2xkt`. The all-open route is IfcOpenShell `IfcConvert` -> GLB, plus `xeokit-metadata` -> JSON, then `convert2xkt -s x.glb -m x.json -o x.xkt`. — [xeokit blog](https://xeokit.io/blog/converting-ifc-to-xkt-using-ifc2gltfcxconverter); [xeokit Notion guide](https://xeokit.notion.site/Converting-IFC-Models-to-XKT-using-Open-Source-Tools-A-Simpler-Pipeline-02d45ba457eb4f808f63bcacb71a4fb3)
  - Strength: very large models and double-precision coordinates (geo-located BIM) [PK].
- **Speckle** (https://github.com/specklesystems): speckle-server is Apache-2.0 "unless stated otherwise". Workspaces and gatekeeper modules fall under an Enterprise Edition licence. Connectors and SDK (speckle-sharp, now the newer `speckle-sharp-connectors`/`speckle-sharp-sdk` repos [PK]) are Apache-2.0. Directories disagree on the server licence ("other"). — [Speckle open-source docs](https://docs.speckle.systems/get-involved/open-source); [opensource.construction](https://opensource.construction/projects/speckle/); [community thread](https://speckle.community/t/permission-to-customize-the-source-code/15250)
  - `@speckle/viewer` (three.js-based) is published on npm. — [yarn](https://classic.yarnpkg.com/en/package/@speckle/viewer)
  - Speckle docs say "compatibility mode" for ACC sync and drag-and-drop ends for every workspace on 1 Nov 2026. — [Speckle dev docs](https://docs.speckle.systems/developers/)
  - Pitfall: Speckle's object model is not IFC. Revit and IFC semantics get flattened into Speckle "Objects" [PK].
- Other [PK]: **IFC.js -> glTF** via IfcConvert (`IfcConvert in.ifc out.glb`). **IfcOpenShell's own web viewer** (`ifcviewer-web`, recent commits add a JS scripting API). — [commit](https://dev.glassvision.dedyn.io/Glassvision/IfcOpenShell/src/commit/89bb3074de8332b500714d19a5310afa4a88918d). **Open CASCADE.js** (LGPL-2.1).

### Inferences
- Stack fit for a commercial SaaS: IfcOpenShell (LGPL; Python import is fine) on the backend, That Open fragments/components (MIT) or three.js + GLB in the browser. Avoid xeokit or PyMuPDF unless you license them.
- For mobile, GLB + three.js / React Three Fiber or native SceneKit/Filament is lighter than web-ifc WASM on low-end devices [inference].

### Gaps
- Did not read the LICENSE files directly for @thatopen/components 3.x or speckle-server EE modules.
- xBIM maintenance status in 2026 was not checked.

---

## 4. Plan-to-3D / plan-to-IFC generators

### Takeaway
No mature open-source tool turns a vector-PDF floor plan into IFC (walls, rooms, doors). The realistic approach is DIY: vector extraction -> shapely polygons -> IfcOpenShell `api` authoring (walls by axis + thickness, IfcSpace from room polygons, IfcOpening + IfcDoor/IfcWindow), then IfcConvert to GLB for viewing. The open projects that exist are raster-based demos (FloorplanToBlender3d, GPL-3) or only partially open (AmpliFy).

### Cited Findings
- **FloorplanToBlender3d** (https://github.com/grebtsew/FloorplanToBlender3d, Python + OpenCV + Blender): GPL-3.0, about 396 stars, 15 open issues. Directories disagree on its activity ("updated June 2026" vs "10 months ago"). There is a Docker image `grebtsew/floorplan-to-blender`. It works on raster images (OpenCV wall detection), not vectors. — [ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2Fgrebtsew%2FFloorplanToBlender3d); [GitHub](https://WWW.GITHUB.COM/grebtsew/FloorplanToBlender3d)
- **AmpliFy** (https://ify.inex.fr): PDF residential plan -> IFC. "Partially open-source": the Python IFC-editing core is on GitHub. Optimised for residential plans and metric scales. — [ify.inex.fr](https://ify.inex.fr)
- An OSArch thread asks for a free way to extrude 2D CAD into IFC walls, doors, windows and slabs. No open answer was found. — [OSArch](https://community.osarch.org/discussion/comment/20546/)
- Reverse direction (useful for synthetic training and test data): **ifc2plan** exports IFC -> PNG + CSV plans. — [GitHub](https://github.com/datarefinerylab/ifc2plan). **BatchPlan** (TU Delft) does batch IFC floor-plan extraction. — [TU Delft repository](https://repository.tudelft.nl/record/uuid:2899ea54-d769-4154-bb04-3c95b018a194)
- **Cloud2BIM** (arXiv 2503.11498): fully open-source point cloud -> IFC. Its IfcOpenShell wall, slab and opening authoring code is a usable reference even though the input differs. — [arXiv](https://arxiv.org/abs/2503.11498v2)
- **Text2BIM** (arXiv 2408.08054; Du, Esser, Nousias, Borrmann, TUM): an LLM multi-agent setup that generates code calling a BIM authoring API (prototyped in Vectorworks). Code at github.com/dcy0577/Text2BIM. — [arXiv](https://arxiv.org/html/2408.08054v1)
- Raster ML datasets and models [PK]: **CubiCasa5k** (dataset CC BY-NC 4.0, i.e. non-commercial; model code MIT), **RPLAN**, **Raster-to-Vector** (Liu et al.), **MLSTRUCT-FP**, **ResPlan**. Check dataset licences. Most forbid commercial use.
- Generic 3D [PK]: **three.js** (MIT) `ExtrudeGeometry` from room or wall polygons; **Blender** (GPL, run headless via bpy); **IfcOpenShell api** (`geometry.create_2pt_wall`, `add_wall_representation`, `add_slab_representation`, `feature.add_feature` for openings) is the recommended authoring layer; **Archilogic** is proprietary with no open equivalent found.

### Inferences
- Generating IFC from detected rooms and walls is straightforward with `ifcopenshell.api`. The hard parts are upstream: turning double-line walls into centerline + thickness, closing room polygons across door gaps, and assigning storey heights, which drawings often don't give (default them, or read sections).
- IFC as the canonical intermediate model gives quantities (ifc5d), LLM querying (IFC-Bench-style agents) and viewers (IfcConvert -> GLB / fragments) for free.

### Gaps
- No vector-PDF-to-IFC open project was confirmed beyond AmpliFy's partial core. The exact AmpliFy GitHub URL and licence were not retrieved.

---

## 5. Text-to-query / LLM over BIM, and MCP servers

### Takeaway
The field moves fast and is research-led, mainly from TUM (Borrmann group). IFC-Bench v1/v2 shows that agents writing IfcOpenShell Python at runtime ("adaptive exploration") beat static query generation, and that model quality matters more than LLM choice. Several MCP servers already exist for IfcOpenShell, Bonsai/Blender and Speckle. They are mostly community-built and young.

### Cited Findings
- **IFC-Bench v1** (EC3 2025, Hellin, Nousias, Borrmann): multi-agent NL retrieval from BIM, 80% overall accuracy across architectural, structural and MEP questions, open dataset. — [EC3 2025](https://ec-3.org/publication/ec32025_265/)
- **IFC-Bench v2 / adaptive exploration** (~May 2026): the agent writes and runs Python against the IFC at runtime. 1,027 tasks over 37 IFC models from 21 projects. Adaptive exploration significantly beats static query generation. — [review summary](https://www.themoonlight.io/review/bim-information-extraction-through-llm-based-adaptive-exploration); [listing](https://newx.sg/paper/detail/a291e9f7-49c1-11f1-b84c-00163e10baa7)
- A journal version compares representations: IfcOpenShell, JSON, SQL, and a property graph with Cypher. One author's summary: BIM model quality matters more than the LLM backbone. — [TUM mediaTUM PDF](https://mediatum.ub.tum.de/doc/1858932/1858932.pdf)
- **IFCMemoryBench** (KDD 2026 workshop): 143 multi-session tasks, 19 projects, 4,016 prior sessions. Accuracy stays below 60%. — [alphaXiv](https://www.alphaxiv.org/abs/2607.26072.md)
- LLM-as-judge for BIM QA validated on 74 IFC-Bench pairs (EC3 2026). — [EC3 2026 PDF](https://ec-3.org/wp-content/uploads/2026/08/EC32026_347.pdf)
- **Text2BIM self-verification** (EC3 2026, Sesterhenn et al.): IDS rules + LLM code checks in a refinement loop; code at github.com/Tsesterh/Text2BIM-Self-Verification. — [EC3 2026](https://ec-3.org/publication/ec32026_444/)
- **BIBIMBAP** benchmark (2026, Kujat et al.): 100 IFC-editing tasks; the best model reached 50.2%. — via [search summary of EC3 2026 listings](https://ec-3.org/?p=15516) (primary page not opened)
- **MCP4IFC** (arXiv 2511.05533, Nithyanantham et al.): MCP server built on IfcOpenShell + Bonsai in Blender for LLM-driven IFC design. — [arXiv](https://arxiv.org/html/2511.05533v1); [project page](https://show2instruct.github.io/mcp4ifc)
- **MCP servers**:
  - `Show2Instruct/bonsai-mcp` (successor to ifc-bonsai-mcp, part of IFC-CoPilot): bridges Claude Desktop, Claude Code, Cursor, VS Code and Codex to a live Blender + Bonsai session on 127.0.0.1:9878. The older build needs Blender 4.4+ and Bonsai 0.8.2+. — [Glama](https://glama.ai/mcp/servers/Show2Instruct/bonsai-mcp); [LobeHub](https://lobehub.com/de/mcp/show2instruct-ifc-bonsai-mcp)
  - `JotaDeRodriguez/Bonsai_mcp`: Blender 4.0+, Python 3.12+, Docker or uv, BlenderMCP-style TCP socket protocol. — [playbooks](https://playbooks.com/mcp/jotaderodriguez-bonsai-blender-ifc)
  - **ifcmcp inside the IfcOpenShell repo** (`src/ifcmcp`, pip-installable, depends on ifcopenshell + `ifcquery` + `ifcedit`). An arXiv comparison says it uses HTTP streaming rather than stdio. — [repo mirror](https://dev.glassvision.dedyn.io/Glassvision/IfcOpenShell/src/tag/bonsai-0.8.6-alpha2608231326/src/ifcmcp); [arXiv 2601.00809](https://arxiv.org/html/2601.00809v1)
  - `bimgeek/speckle-mcp` (Python, needs SPECKLE_TOKEN): manages projects, models and versions through natural language. It does not transfer geometry. — [mcpservers.org](https://mcpservers.org/servers/bimgeek/speckle-mcp)
  - Speckle's own position: raw-data MCP access makes the LLM rebuild context on every query, so Speckle favours a curated "context layer". — [Speckle blog](https://speckle.systems/blog/ai-in-aec-has-an-access-problem-solved-and-a-trust-problem-unsolved/)
  - IFC-CoPilot paper (Sesterhenn). — [PDF](https://tsesterh.github.io/papers/IFC-Copilot.pdf)

### Inferences
- For "ask the takeoff" features, give the LLM a sandboxed IfcOpenShell Python tool plus a precomputed quantity table (SQL/JSON), not raw IFC text. The benchmarks favour runtime code exploration, and accuracy limits come from the data. Clean, well-classified models (correct IfcSpace / IfcDoor) matter most.
- The existing MCP servers are useful for prototyping. The Bonsai ones need a running Blender, which doesn't fit a server-side SaaS. The pip-installable `ifcmcp` is the most deployable.

### Gaps
- Licences of the individual MCP repos were not checked (likely MIT/GPL mixes; Bonsai itself is GPL because Blender add-ons are GPL [PK]).
- arXiv IDs for IFC-Bench v1/v2 were not confirmed.

---

## 6. Geometry libraries (area, perimeter, polygon ops)

### Takeaway
Shapely 2.x (BSD-3) over GEOS (LGPL-2.1) is the standard in Python. turf.js (MIT) and Clipper2 (Boost) cover JS and robust offset/boolean ops. All are commercial-friendly. [Whole section PK: canonical URLs, not re-verified this session.]

### Cited Findings
- **Shapely** — https://github.com/shapely/shapely — BSD-3, Python, vectorised 2.x API (`area`, `length`, `buffer`, `polygonize`, `unary_union`, `make_valid`, STRtree). [PK]
- **GEOS** — https://libgeos.org — LGPL-2.1, C/C++; the engine behind Shapely, PostGIS and QGIS. [PK]
- **turf.js** — https://github.com/Turfjs/turf — MIT. Pitfall: it assumes WGS84 lon/lat, so `turf.area` returns geodesic m² and is wrong for planar drawing coordinates. Use planar math or Clipper/JSTS instead. [PK]
- **Clipper2** — https://github.com/AngusJohnson/Clipper2 — Boost Software License. C++/C#/Delphi with JS/Python ports (e.g. `pyclipr`, `clipper2-js`). Integer-robust booleans and offsets (wall thickness to centerline, inward offsets for finish areas). [PK]
- **JSTS** (EPL/EDL, JS port of JTS) and **polygon-clipping** (MIT, JS). **CGAL** (GPL/LGPL + commercial) for heavy straight-skeleton / medial-axis work (deriving wall centerlines from double lines). **scikit-geometry** (CGAL bindings). [PK]
- **NetworkX** (BSD) for wall-graph / room-adjacency graphs. **rtree** / Shapely STRtree for spatial indexing. [PK]

### Inferences
- Use `shapely.polygonize` on cleaned wall-face line segments (snap endpoints with a tolerance) to get room polygons, then bridge door gaps by closing openings with segments across the jamb. Use `make_valid` after any snapping. Always convert PDF points (1/72 in) to real units with the detected scale before computing area.

### Gaps
- None of this section was re-verified via search this session. Confirm current versions and licences.

---

## Licence cheat-sheet (commercial closed-source SaaS)
- Safe / permissive: ezdxf (MIT), pdfplumber/pdfminer.six (MIT) [PK], pdf.js (Apache-2.0) [PK], pypdfium2 (Apache/BSD) [PK], @thatopen/fragments (MIT), @thatopen/components 3.x (MIT, per third party), three.js (MIT) [PK], Shapely (BSD), turf (MIT), Clipper2 (Boost), Speckle core/connectors (Apache-2.0, minus EE modules).
- Weak copyleft (fine if used unmodified as a library, with notices): IfcOpenShell (LGPL-3+), GEOS (LGPL-2.1), web-ifc (MPL-2.0), xBIM (CDDL) [PK].
- Strong copyleft / needs care: LibreDWG (GPL-3; isolate as a CLI), FloorplanToBlender3d (GPL-3), Bonsai/Blender (GPL), Poppler (GPL).
- Network copyleft or dual-licensed (buy a licence for closed SaaS): PyMuPDF/MuPDF (AGPL or Artifex commercial), xeokit (AGPL or commercial).
- Proprietary freeware: ODA File Converter (EULA unverified), Creoox ifc2gltfcxconverter (closed).
- Non-commercial data: CubiCasa5k dataset (CC BY-NC) [PK].
