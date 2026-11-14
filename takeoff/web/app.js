// Takeoff UI: projects -> plan viewer with traceable elements -> chat answers computed by the engine.
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const SVGNS = "http://www.w3.org/2000/svg";
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (v, d = 2) => (v == null ? "–" : Number.isInteger(v) ? String(v) : Number(v).toFixed(d));

const KIND_LABEL = { room: "Rooms", door: "Doors", window: "Windows", fixture: "Fixtures", unit: "Apartments", floor: "Floor plans" };
const SUB_LABEL = { shaft: "Shaft / duct", storage: "Storage", corridor: "Corridor", wc: "WC / toilet", washbasin: "Washbasin", sink: "Sink", bathtub: "Bathtub", shower: "Shower", kitchen: "Kitchen",
  sauna_stove: "Sauna stove", bedroom: "Bedroom", bathroom: "Bathroom", balcony: "Balcony", sauna: "Sauna" };
const COLORS = { other: "var(--muted)", room: "var(--room)", door: "var(--door)", window: "var(--window)", fixture: "var(--fixture)", unit: "var(--unit)", wall: "var(--muted)" };
const LAYERS = ["room", "door", "window", "fixture", "unit"];

const S = {
  projects: [], path: null, b: null, bg: null, level: null,
  layers: Object.fromEntries(LAYERS.map((k) => [k, true])),
  hl: new Set(), sel: null, history: [], vb: null, three: null,
};

// ---------- icons (Lucide, MIT) ----------
const ICONS = {
  logo: '<path d="M12 3 21 12 12 21 3 12Z"/><path d="M12 8v8M8 12h8"/>',
  chevron: '<path d="m6 9 6 6 6-6"/>',
  map: '<path d="M14.106 5.553a2 2 0 0 0 1.788 0l3.659-1.83A1 1 0 0 1 21 4.619v12.764a1 1 0 0 1-.553.894l-4.553 2.277a2 2 0 0 1-1.788 0l-4.212-2.106a2 2 0 0 0-1.788 0l-3.659 1.83A1 1 0 0 1 3 19.381V6.618a1 1 0 0 1 .553-.894l4.553-2.277a2 2 0 0 1 1.788 0z"/><path d="M15 5.764v15"/><path d="M9 3.236v15"/>',
  box: '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
  list: '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
  check: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  sparkles: '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
  chat: '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
  send: '<path d="m5 12 7-7 7 7"/><path d="M12 19V5"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  fit: '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
};
const icon = (n) => `<svg class="i" viewBox="0 0 24 24" aria-hidden="true">${ICONS[n] || ""}</svg>`;
function paintIcons(root = document) { for (const el of $$("i[data-icon]", root)) el.outerHTML = icon(el.dataset.icon); }
paintIcons();

// ---------- projects ----------
async function loadProjects() {
  S.projects = await (await fetch("/api/projects")).json();
  renderProjects();
}
function renderProjects() {
  const q = $("#search").value.toLowerCase();
  const groups = {};
  for (const p of S.projects) if (!q || p.name.toLowerCase().includes(q)) (groups[p.group] ??= []).push(p);
  $("#project-list").innerHTML = Object.entries(groups).map(([g, ps]) =>
    `<div class="group-head">${esc(g)} · ${ps.length}</div>` +
    ps.map((p) => `<button class="proj ${p.path === S.path ? "active" : ""}" data-path="${esc(p.path)}">
      <span class="fmt">${esc(p.format)}</span><span class="nm" title="${esc(p.name)}">${esc(p.name)}</span></button>`).join("")
  ).join("") || `<div class="panel-note">No drawings match.</div>`;
}
const openPicker = () => { $("#picker").classList.remove("hidden"); renderProjects(); setTimeout(() => $("#search").focus(), 30); };
const closePicker = () => $("#picker").classList.add("hidden");
$("#project-list").addEventListener("click", (e) => {
  const b = e.target.closest(".proj");
  if (b) { closePicker(); openProject(b.dataset.path); }
});
$("#search").addEventListener("input", renderProjects);
$("#btn-projects").addEventListener("click", openPicker);
$("#btn-projects-m").addEventListener("click", openPicker);
$("#picker-close").addEventListener("click", closePicker);
$("#picker").addEventListener("click", (e) => { if (e.target.id === "picker") closePicker(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closePicker(); });
async function upload(e) {
  const f = e.target.files[0];
  if (!f) return;
  const fd = new FormData(); fd.append("file", f);
  toast(`Reading ${f.name}…`);
  const r = await fetch("/api/upload", { method: "POST", body: fd });
  if (!r.ok) { toast((await r.json()).detail || "Upload failed"); return; }
  const { path } = await r.json();
  await loadProjects();
  openProject(path);
}
$("#upload").addEventListener("change", upload);
$("#upload-m").addEventListener("change", upload);

async function openProject(path) {
  S.path = path; S.hl.clear(); S.sel = null; S.history = []; S.bg = null;
  renderProjects();
  $("#plan-empty").classList.add("hidden");
  $("#plan-loading").classList.remove("hidden");
  $("#inspector").classList.add("hidden");
  const r = await fetch(`/api/building?path=${encodeURIComponent(path)}`);
  if (!r.ok) {
    $("#plan-loading").classList.add("hidden");
    $("#plan-empty").textContent = (await r.json()).detail || "Could not read this drawing";
    $("#plan-empty").classList.remove("hidden");
    return;
  }
  const b = await r.json();
  if (S.path !== path) return;
  S.b = b;
  S.index = Object.fromEntries(b.elements.map((e) => [e.id, e]));
  if (b.view.background_kind === "vector") S.bg = await (await fetch(b.view.background)).json();
  const name = S.projects.find((p) => p.path === path)?.name || b.id;
  $("#project-title").textContent = name;
  $("#project-title-m").textContent = name;
  $("#interp-pill").textContent = b.interpreter === "claude" ? "Chat: Claude + engine" : "Chat: keyword parser";
  $("#interp-dot").classList.toggle("on", b.interpreter === "claude");
  // hosted demo: prepared drawings only (importing needs the local version), and credit the data
  $$(".sidebar .import, .mobile-top label.icon-btn").forEach((el) => el.classList.toggle("hidden", !!b.demo));
  if (b.demo) $("#interp-pill").textContent += " · demo";
  setupLevels();
  renderToggles();
  drawPlan(true);
  await loadRules();
  renderAll();
  resetChat();
  $("#plan-loading").classList.add("hidden");
  if (S.three) S.three.load(S.b, S.bg, Number($("#height").value));
}

// ---------- plan viewer ----------
const svg = $("#plan-svg");
const pt = (p) => (S.b.view.flip_y ? [p[0], -p[1]] : [p[0], p[1]]);

function setupLevels() {
  const sel = $("#level-select");
  const levels = [...new Set(S.b.elements.filter((e) => e.polygon && e.level).map((e) => e.level))];
  S.level = levels.length > 1 ? levels[0] : null;
  sel.classList.toggle("hidden", levels.length < 2);
  sel.innerHTML = levels.map((l) => `<option>${esc(l)}</option>`).join("");
}
$("#level-select").addEventListener("change", (e) => { S.level = e.target.value; drawPlan(true); });

function renderToggles() {
  const present = new Set(S.b.elements.filter((e) => e.polygon).map((e) => e.kind));
  $("#layer-toggles").innerHTML = LAYERS.filter((k) => present.has(k)).map((k) =>
    `<button class="lt ${S.layers[k] ? "" : "off"}" data-k="${k}"><i style="background:${COLORS[k]}"></i><span>${KIND_LABEL[k]}</span></button>`).join("");
}
$("#layer-toggles").addEventListener("click", (e) => {
  const b = e.target.closest(".lt");
  if (!b) return;
  S.layers[b.dataset.k] = !S.layers[b.dataset.k];
  renderToggles(); drawPlan(false);
});

function visibleEls() {
  return S.b.elements.filter((e) => e.polygon && e.polygon.length >= 3 &&
    (S.layers[e.kind] ?? true) && (!S.level || !e.level || e.level === S.level) &&
    !(e.kind === "floor" && e.polygon.every((p) => p[0] === 0 && p[1] === 0)));
}

function drawPlan(fit) {
  const bg = $("#bg-layer"), lay = $("#el-layer");
  bg.innerHTML = ""; lay.innerHTML = "";
  const v = S.b.view;
  if (v.background_kind === "image") {
    const img = document.createElementNS(SVGNS, "image");
    img.setAttribute("href", v.background);
    img.setAttribute("width", v.image_size[0]); img.setAttribute("height", v.image_size[1]);
    img.setAttribute("class", "bg-image");
    bg.appendChild(img);
  } else if (S.bg) {
    for (const [layer, ds] of Object.entries(S.bg.layers)) {
      if (layer === "ROOM_TEXT") continue;
      const p = document.createElementNS(SVGNS, "path");
      p.setAttribute("d", ds.join(" "));
      p.setAttribute("class", `bg-line bg-${layer}`);
      if (layer === "WALL") p.setAttribute("fill-rule", "nonzero");
      bg.appendChild(p);
    }
  }
  const els = visibleEls();
  const order = { unit: 0, room: 1, floor: 2, fixture: 3, window: 4, door: 5 };
  els.sort((a, b) => (order[a.kind] ?? 9) - (order[b.kind] ?? 9));
  const frag = document.createDocumentFragment();
  for (const e of els) {
    const poly = document.createElementNS(SVGNS, "polygon");
    poly.setAttribute("points", e.polygon.map((p) => pt(p).join(",")).join(" "));
    poly.setAttribute("class", `el ${e.kind}${e.flags.length ? " flagged" : ""}`);
    poly.dataset.id = e.id;
    frag.appendChild(poly);
  }
  // room labels (vector sources carry names and areas)
  if (S.b.view.flip_y) for (const e of els.filter((e) => e.kind === "room" && (e.name || e.area_m2))) {
    const c = centroid(e.polygon.map(pt));
    const bb = bounds(e.polygon.map(pt));
    const t = document.createElementNS(SVGNS, "text");
    t.dataset.w = Math.min(bb.x1 - bb.x0, (bb.y1 - bb.y0) * 2.5);
    t.setAttribute("x", c[0]); t.setAttribute("y", c[1]);
    t.setAttribute("class", "room-label");
    t.innerHTML = `<tspan x="${c[0]}" dy="0">${esc(e.name || "")}</tspan>` +
      (e.area_m2 ? `<tspan class="a" x="${c[0]}" dy="1.2em">${fmt(e.area_m2)} m²</tspan>` : "");
    frag.appendChild(t);
  }
  lay.appendChild(frag);
  applyHighlight();
  if (fit || !S.vb) fitView(); else setVB();
}

function centroid(pts) {
  let x = 0, y = 0;
  for (const p of pts) { x += p[0]; y += p[1]; }
  return [x / pts.length, y / pts.length];
}
function bounds(pts) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  return { x0, y0, x1, y1 };
}
function fitView(pts) {
  let bb;
  if (pts) bb = bounds(pts);
  else if (S.b.view.background_kind === "image") bb = { x0: 0, y0: 0, x1: S.b.view.image_size[0], y1: S.b.view.image_size[1] };
  else {
    const all = visibleEls().flatMap((e) => e.polygon.map(pt));
    bb = all.length ? bounds(all) : { x0: 0, y0: 0, x1: 10, y1: 10 };
  }
  const r = svg.getBoundingClientRect();
  const w = bb.x1 - bb.x0 || 1, h = bb.y1 - bb.y0 || 1, pad = pts ? 0.6 : 0.04;
  let vw = w * (1 + 2 * pad), vh = h * (1 + 2 * pad);
  const ar = (r.width || 800) / (r.height || 600);
  if (vw / vh < ar) vw = vh * ar; else vh = vw / ar;
  S.vb = { x: (bb.x0 + bb.x1) / 2 - vw / 2, y: (bb.y0 + bb.y1) / 2 - vh / 2, w: vw, h: vh };
  setVB();
}
function setVB() {
  const { x, y, w, h } = S.vb;
  svg.setAttribute("viewBox", `${x} ${y} ${w} ${h}`);
  // keep label size constant on screen
  const k = w / (svg.getBoundingClientRect().width || 800);
  svg.style.setProperty("--k", k);
  for (const t of $$(".room-label", svg)) {
    t.style.fontSize = `${11 * k}px`; t.style.strokeWidth = `${3 * k}px`;
    t.style.display = Number(t.dataset.w) / k < 64 ? "none" : "";  // hide labels that would not fit their room
  }
}
$("#btn-fit").addEventListener("click", () => (S.b && fitView()));
window.addEventListener("resize", () => S.b && setVB());

// pan / zoom / pinch / click
const pointers = new Map();
let drag = null;
function toSvg(cx, cy) {
  const r = svg.getBoundingClientRect();
  return [S.vb.x + ((cx - r.left) / r.width) * S.vb.w, S.vb.y + ((cy - r.top) / r.height) * S.vb.h];
}
function zoomAt(cx, cy, f) {
  const [sx, sy] = toSvg(cx, cy);
  S.vb = { x: sx - (sx - S.vb.x) * f, y: sy - (sy - S.vb.y) * f, w: S.vb.w * f, h: S.vb.h * f };
  setVB();
}
svg.addEventListener("wheel", (e) => { if (!S.vb) return; e.preventDefault(); zoomAt(e.clientX, e.clientY, Math.exp(e.deltaY * 0.0015)); }, { passive: false });
svg.addEventListener("pointerdown", (e) => {
  if (!S.vb) return;
  svg.setPointerCapture(e.pointerId);
  pointers.set(e.pointerId, [e.clientX, e.clientY]);
  drag = { x: e.clientX, y: e.clientY, vb: { ...S.vb }, moved: false, target: e.target, pinch: null };
  if (pointers.size === 2) {
    const [a, b] = [...pointers.values()];
    drag.pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), cx: (a[0] + b[0]) / 2, cy: (a[1] + b[1]) / 2 };
  }
});
svg.addEventListener("pointermove", (e) => {
  if (!drag || !pointers.has(e.pointerId)) return;
  pointers.set(e.pointerId, [e.clientX, e.clientY]);
  if (pointers.size === 2 && drag.pinch) {
    const [a, b] = [...pointers.values()];
    const d = Math.hypot(a[0] - b[0], a[1] - b[1]);
    zoomAt(drag.pinch.cx, drag.pinch.cy, drag.pinch.d / d);
    drag.pinch.d = d; drag.moved = true;
    return;
  }
  const r = svg.getBoundingClientRect();
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if (Math.abs(dx) + Math.abs(dy) > 4) { drag.moved = true; svg.classList.add("panning"); }
  if (drag.moved) {
    S.vb = { ...drag.vb, x: drag.vb.x - (dx / r.width) * drag.vb.w, y: drag.vb.y - (dy / r.height) * drag.vb.h };
    setVB();
  }
});
const endPtr = (e) => {
  pointers.delete(e.pointerId);
  svg.classList.remove("panning");
  if (drag && !drag.moved && pointers.size === 0) {
    const el = drag.target.closest?.(".el");
    select(el ? el.dataset.id : null);
  }
  if (pointers.size === 0) drag = null;
};
svg.addEventListener("pointerup", endPtr);
svg.addEventListener("pointercancel", endPtr);

function applyHighlight() {
  const any = S.hl.size > 0;
  for (const p of $$(".el", svg)) {
    p.classList.toggle("hl", S.hl.has(p.dataset.id));
    p.classList.toggle("sel", p.dataset.id === S.sel);
    p.classList.toggle("dim", any && !S.hl.has(p.dataset.id) && !p.classList.contains("unit") && !p.classList.contains("room"));
  }
  S.three?.highlight(S.hl);
}
function highlight(ids, zoom = false) {
  S.hl = new Set(ids);
  // a highlighted element on another level: jump to that level
  const lv = ids.map((i) => S.index[i]?.level).find((l) => l);
  if (S.level && lv && lv !== S.level && !ids.some((i) => S.index[i]?.level === S.level)) {
    S.level = lv; $("#level-select").value = lv; drawPlan(true);
  }
  applyHighlight();
  if (zoom) {
    const pts = ids.map((i) => S.index[i]).filter((e) => e?.polygon).flatMap((e) => e.polygon.map(pt));
    if (pts.length) requestAnimationFrame(() => fitView(pts));  // after a view switch the plan has just become visible
  }
}

function select(id) {
  S.sel = id;
  applyHighlight();
  const box = $("#inspector");
  const e = id && S.index[id];
  if (!e) { box.classList.add("hidden"); return; }
  const rows = [
    ["Type", `${e.kind}${e.subtype ? " · " + (SUB_LABEL[e.subtype] || e.subtype) : ""}`],
    e.name && ["Label", e.name], e.number && ["Number", e.number], e.unit && ["Apartment", e.unit], e.level && ["Level", e.level],
    e.area_m2 != null && ["Area", `${fmt(e.area_m2)} m²`], e.written_area_m2 != null && ["Written on plan", `${fmt(e.written_area_m2)} m²`],
    e.length_m != null && ["Length", `${fmt(e.length_m)} m`], e.volume_m3 != null && ["Volume", `${fmt(e.volume_m3)} m³`],
    ["Confidence", `${Math.round(e.confidence * 100)}%`],
    ["Source", `<span class="mono">${esc(e.source.method)}${e.source.layer ? " · " + esc(e.source.layer) : ""}${e.source.ref ? " · " + esc(e.source.ref) : ""}</span>`],
  ].filter(Boolean);
  box.innerHTML = `<h4><span>${esc(e.name || KIND_LABEL[e.kind]?.replace(/s$/, "") || e.kind)}</span><button class="close" aria-label="Close">✕</button></h4>
    <dl class="kv">${rows.map(([k, v]) => `<dt>${k}</dt><dd>${typeof v === "string" && v.startsWith("<") ? v : esc(v)}</dd>`).join("")}</dl>
    ${e.flags.length ? `<ul class="flags">${e.flags.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}`;
  box.classList.remove("hidden");
  $(".close", box).onclick = () => select(null);
}

// ---------- views ----------
const VIEWS = {
  plan: ["Plan", "Every element is clickable and traced to the drawing"],
  "3d": ["3D model", "Extruded from the plan · heights are assumed, not measured"],
  takeoff: ["Takeoff", "Quantities counted and measured from the drawing"],
  review: ["Review", "Uncertain items wait for you instead of being guessed"],
  rules: ["Learned rules", "What your reviews have taught the system"],
};
const PANES = { plan: "#plan-view", "3d": "#three-view", takeoff: "#takeoff", review: "#review", rules: "#rules" };
const isPhone = () => innerWidth <= 900;
async function setView(v) {
  if (v === "chat" && !isPhone()) { $("#ask-input").focus(); return; }
  $("#app").dataset.view = v;
  $$(".nav-item[data-view], .bottom-nav button").forEach((b) => b.classList.toggle("active", b.dataset.view === v));
  if (v !== "plan") $("#back-pill").classList.add("hidden");
  if (v === "chat") { requestAnimationFrame(() => { const m = $("#messages"); m.scrollTop = m.scrollHeight; }); return; }
  for (const [k, sel] of Object.entries(PANES)) $(sel).classList.toggle("hidden", k !== v);
  $("#view-title").textContent = VIEWS[v][0];
  $("#view-sub").textContent = VIEWS[v][1];
  $("#plan-tools").classList.toggle("hidden", v !== "plan");
  $("#three-tools").classList.toggle("hidden", v !== "3d");
  if (v === "plan") requestAnimationFrame(() => S.b && setVB());
  if (v === "3d") {
    if (!S.three) {
      const m = await import("./three3d.js");
      S.three = m.create($("#three-canvas"), (id) => select(id));
    }
    if (S.b) S.three.load(S.b, S.bg, Number($("#height").value));
    S.three.resize();
    S.three.highlight(S.hl);
  }
}
// on a phone, jumping from an answer to the plan leaves a pill to jump back
const showOnPlan = () => {
  const from = $("#app").dataset.view;
  if (from !== "plan") setView("plan");
  $("#back-pill").classList.toggle("hidden", !(isPhone() && from === "chat"));
};
$("#back-pill").addEventListener("click", () => { $("#back-pill").classList.add("hidden"); setView("chat"); });
$$(".nav-item[data-view], .bottom-nav button").forEach((b) => b.addEventListener("click", () => setView(b.dataset.view)));
$("#height").addEventListener("change", () => S.three && S.b && S.three.load(S.b, S.bg, Number($("#height").value)));

function renderAll() { renderStats(); renderTakeoff(); renderReview(); renderRules(); }

function renderStats() {
  const els = S.b.elements, m = S.b.view.units === "m";
  const n = (k, sub) => els.filter((e) => e.kind === k && (!sub || e.subtype === sub)).length;
  const rooms = els.filter((e) => e.kind === "room");
  const area = rooms.reduce((a, e) => a + (e.area_m2 || 0), 0);
  const fx = els.filter((e) => e.kind === "fixture");
  const open = els.filter((e) => e.flags.length && !e.reviewed).length;
  const wc = fx.filter((e) => e.subtype === "wc").length;
  const cards = [
    ["Rooms", rooms.length, m && area ? `${fmt(area, 1)} m² floor area` : `${S.b.levels.length || 1} floor${S.b.levels.length > 1 ? "s" : ""}`],
    ["Doors · windows", `${n("door")} · ${n("window")}`, "counted from the drawing"],
    ["Fixtures", fx.length, fx.length ? `${wc} WC · ${fx.length - wc} other` : "none detected"],
    ["To review", open, open ? "waiting for a decision" : "nothing uncertain", open ? "attn clickable" : "clickable", "review"],
  ];
  $("#stats").innerHTML = cards.map(([k, v, sub, cls = "", go = ""]) =>
    `<div class="stat ${cls}" ${go ? `data-go="${go}"` : ""}><div class="k">${esc(k)}</div><div class="v">${esc(v)}</div><div class="s">${esc(sub)}</div></div>`).join("");
}
$("#stats").addEventListener("click", (e) => { const c = e.target.closest("[data-go]"); if (c) setView(c.dataset.go); });

// ---------- chat ----------
function suggestions() {
  const t = S.b?.source_type;
  if (t === "swiss_dxf") {
    const u = S.b.elements.find((e) => e.kind === "unit")?.name;
    return ["How many doors?", "How many toilets?", u && `What is the area of apartment ${u}?`, "How many windows?", "Wall tile area of the bathrooms"].filter(Boolean);
  }
  if (t === "ifc") return ["How many doors are in the model?", "How many windows?", "Total wall length", "How many rooms?"];
  return ["How many doors?", "How many toilets?", "How many bedrooms?", "How many windows?", "How many saunas?"];
}
function resetChat() {
  $("#messages").innerHTML = `<div class="hint"><p><b>Ask about this drawing.</b> Every number is counted or measured by code from the drawing, never guessed. Open <i>How it was calculated</i> to see each element used.</p><div class="chips">${suggestions().map((s) => `<button class="chip">${esc(s)}</button>`).join("")}</div></div>`;
}
$("#messages").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (chip) { ask(chip.textContent); return; }
  const elb = e.target.closest("[data-el]");
  if (elb) { showOnPlan(); highlight([elb.dataset.el], true); select(elb.dataset.el); return; }
  const all = e.target.closest("[data-show]");
  if (all) { showOnPlan(); highlight(JSON.parse(all.dataset.show), true); }
});
$("#messages").addEventListener("mouseover", (e) => {
  const elb = e.target.closest("[data-el]");
  if (elb) { S.hl = new Set([elb.dataset.el]); applyHighlight(); }
});
$("#ask-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const v = $("#ask-input").value.trim();
  if (v) ask(v);
});

async function ask(question) {
  if (!S.b) return;
  $("#ask-input").value = "";
  const box = $("#messages");
  box.insertAdjacentHTML("beforeend", `<div class="msg-user">${esc(question)}</div><div class="msg-bot pending"><div class="spinner"></div>Reading the drawing…</div>`);
  box.scrollTop = box.scrollHeight;
  const pending = box.lastElementChild;
  let res;
  try {
    const r = await fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: S.path, question, history: S.history, height_m: Number($("#height").value) || null }) });
    res = await r.json();
    if (!r.ok) throw new Error(res.detail || "error");
  } catch (err) {
    pending.outerHTML = `<div class="msg-bot"><span class="tag bad">Error</span> ${esc(err.message)}</div>`;
    return;
  }
  S.history.push({ role: "user", content: question });
  if (!res.understood) {
    pending.outerHTML = `<div class="msg-bot">${esc(res.message)}</div>`;
    S.history.push({ role: "assistant", content: res.message });
    return;
  }
  const results = res.results || [{ label: "Result", query: res.query, answer: res.answer }];
  const unitOf = (a, q) => ({ count: "", m2: "m²", m3: "m³", m: "m" }[a.unit] ?? a.unit) || (a.unit === "count" ? describeQuery(q) : "");
  const confTag = (a) => { const c = Math.round(a.confidence * 100);
    return a.value == null ? `<span class="tag bad">needs a human</span>` : `<span class="tag ${c >= 90 ? "good" : "warn"}">${c}% confidence</span>`; };
  const qchips = (q) => Object.entries(q).map(([k, v]) => `<span>${esc(k)}=${esc(Array.isArray(v) ? v.join("|") : v)}</span>`).join("");
  const elsOf = (a) => a.elements.map((id) => S.index[id]).filter(Boolean);
  const detail = (r) => { const a = r.answer, els = elsOf(a);
    return `<h5>Question read as</h5><div class="qchips">${qchips(r.query)}</div>
      <h5>Steps</h5><ol class="steps">${a.steps.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>
      ${els.length ? `<h5>Elements used (${els.length})</h5><div class="el-list">${els.slice(0, 120).map((e) => `<button data-el="${esc(e.id)}">${esc(e.name || e.number || e.subtype || e.id)}</button>`).join("")}${els.length > 120 ? `<span class="note">+${els.length - 120} more</span>` : ""}</div>` : ""}
      ${a.flags.length ? `<h5>Check by a human</h5><ul class="flags">${a.flags.slice(0, 30).map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}`; };
  const allIds = [...new Set(results.flatMap((r) => r.answer.elements))];
  const flags = results.reduce((n, r) => n + r.answer.flags.length, 0);
  const showBtn = allIds.some((id) => S.index[id]?.polygon) ? `<button class="tag" data-show='${esc(JSON.stringify(allIds))}'>Show on plan</button>` : "";
  let head;
  if (results.length === 1) {
    const r = results[0], a = r.answer;
    head = `<div class="ans-value">${a.value == null ? "Can't tell" : esc(fmt(a.value))}<small>${esc(unitOf(a, r.query))}</small></div>
      <div class="ans-meta">${confTag(a)}${flags ? `<span class="tag warn">${flags} to check</span>` : ""}${showBtn}</div>`;
  } else {
    const max = Math.max(...results.map((r) => r.answer.value || 0)) || 1;
    head = `<div class="ans-rows">${results.map((r) => `<button class="ans-row" data-show='${esc(JSON.stringify(r.answer.elements))}'>
        <span class="lbl">${esc(r.label)}</span><span class="val">${r.answer.value == null ? "–" : esc(fmt(r.answer.value))}<small>${esc(unitOf(r.answer, r.query))}</small></span>
        <i class="bar" style="width:${Math.max(2, ((r.answer.value || 0) / max) * 100)}%"></i></button>`).join("")}</div>
      <div class="ans-meta">${confTag({ value: 1, confidence: Math.min(...results.map((r) => r.answer.confidence)) })}${flags ? `<span class="tag warn">${flags} to check</span>` : ""}${showBtn}</div>`;
  }
  pending.outerHTML = `<div class="msg-bot">${head}
    ${res.note ? `<div class="note">${esc(res.note)}</div>` : ""}
    <details class="reason"><summary>How it was calculated</summary>
      <div class="note">Read by ${esc(res.interpreter)}; every number computed by the engine from the drawing.</div>
      ${results.length === 1 ? detail(results[0]) : results.map((r) => `<div class="sub-res"><h5 class="res-h">${esc(r.label)}</h5>${detail(r)}</div>`).join("")}
    </details></div>`;
  S.history.push({ role: "assistant", content: results.map((r) => `${r.label}: ${fmt(r.answer.value)} ${r.answer.unit}`).join("; ") });
  highlight(allIds);
  box.scrollTop = box.scrollHeight;
}
function describeQuery(q) {
  const s = q.subtype ? SUB_LABEL[q.subtype] || q.subtype : KIND_LABEL[q.kind] || q.kind;
  return String(s).toLowerCase();
}

// ---------- takeoff ----------
function renderTakeoff() {
  const s = S.b.summary;
  const label = (r) => r.subtype ? (SUB_LABEL[r.subtype] || r.subtype) : (KIND_LABEL[r.kind] || r.kind);
  const max = Math.max(1, ...s.rows.map((r) => r.count));
  $("#takeoff").innerHTML = `<table class="tbl"><thead><tr><th>Item</th><th class="num">Qty</th><th class="num">Area</th></tr></thead><tbody>
    ${s.rows.map((r, i) => `<tr class="clickable" data-i="${i}"><td><span class="sw" style="background:${COLORS[r.kind] || "var(--muted)"}"></span>${esc(label(r))}
        <div class="bar" style="width:${Math.max(2, (r.count / max) * 100)}%;background:${COLORS[r.kind] || "var(--muted)"}"></div></td>
      <td class="num">${r.count}</td><td class="num">${r.area_m2 != null ? fmt(r.area_m2) + " m²" : ""}</td></tr>`).join("")}
    </tbody></table>
    <div class="panel-note">${s.elements} elements read from <span class="mono">${esc(S.b.source_type)}</span>. Click a row to see it on the plan.
      ${S.b.source_type === "raster" ? " Scans have no verified scale, so areas are not given." : ""}</div>
    ${S.b.credit ? `<div class="panel-note">Drawing: ${esc(S.b.credit)}</div>` : ""}
    <div class="pane-actions"><button class="btn" id="export-csv">${icon("download")}Export element list (CSV)</button></div>`;
  $$("#takeoff tr.clickable").forEach((tr) => tr.addEventListener("click", () => {
    const r = s.rows[tr.dataset.i];
    const ids = S.b.elements.filter((e) => e.kind === r.kind && (r.subtype == null || e.subtype === r.subtype)).map((e) => e.id);
    setView("plan"); highlight(ids, true);
  }));
  $("#export-csv").addEventListener("click", exportCsv);
}
function exportCsv() {
  const cols = ["id", "kind", "subtype", "name", "number", "unit", "level", "area_m2", "length_m", "volume_m3", "confidence", "flags", "source"];
  const q = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const rows = S.b.elements.map((e) => cols.map((c) => q(c === "flags" ? e.flags.join("; ") : c === "source" ? `${e.source.method} ${e.source.ref || ""}` : e[c])).join(","));
  const blob = new Blob([cols.join(",") + "\n" + rows.join("\n")], { type: "text/csv" });
  const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: `${S.b.id}-takeoff.csv` });
  a.click();
}

// ---------- review queue + learning loop ----------
// Decisions go to the server; labelling an element teaches a rule that applies to every drawing.
let RULES = { rules: [], labels: {} };
async function loadRules() { RULES = await (await fetch("/api/rules")).json(); }
const ruleOf = (id) => RULES.rules.find((r) => r.id === id);
const what = (e) => e.name || (e.number ? `Room ${e.number}` : "") || (e.subtype ? (RULES.labels[e.subtype] || SUB_LABEL[e.subtype] || e.subtype) : e.kind);
const area = (e) => (e.area_m2 != null && S.b.view.units === "m" ? ` · ${fmt(e.area_m2)} m²` : "");
const J = (v) => esc(JSON.stringify(v));
const labelChips = (ids) => `<div class="label-q">What is it?</div><div class="chips">${Object.entries(RULES.labels).map(([k, v]) =>
  `<button class="chip" data-label="${k}" data-ids='${J(ids)}'>${esc(v)}</button>`).join("")}
  <button class="chip" data-label="?" data-ids='${J(ids)}'>Other…</button>
  <button class="chip" data-dec="ok" data-ids='${J(ids)}'>Fine as is</button></div>`;
function setBadge(sel, n) { const b = $(sel); b.textContent = n; b.toggleAttribute("data-zero", !n); }

function renderReview() {
  const els = S.b.elements;
  const open = els.filter((e) => e.flags.length && !e.reviewed);
  const groups = {}, single = [];
  for (const e of open) (e.classified_by ? (groups[e.classified_by] ??= []) : single).push(e);
  const done = els.filter((e) => e.reviewed);
  setBadge("#review-badge", open.length); setBadge("#review-badge-m", open.length);
  const groupHtml = Object.entries(groups).map(([rid, es]) => {
    const r = ruleOf(rid), ids = es.map((e) => e.id);
    return `<div class="rv">
      <h4><span>${es.length} × ${esc(RULES.labels[r?.label] || r?.label || "classified")}<span class="tag warn">auto · ${r ? Math.round(r.confidence * 100) : "?"}%</span></span>
        <button class="link" data-goto='${J(ids)}'>Show</button></h4>
      <div class="rule-txt">${esc(r?.text || rid)}</div>
      <div class="acts"><button class="btn primary" data-dec="ok" data-ids='${J(ids)}'>Confirm all ${es.length}</button>
        <button class="btn" data-expand="${esc(rid)}">One by one</button></div>
      <div class="sub-list hidden" id="sub-${esc(rid)}">${es.map((e) => `<div class="sub-row">
        <button class="link" data-goto='${J([e.id])}'>${esc(e.number || e.id)}${area(e)}</button>
        <span><button class="mini" data-dec="ok" data-ids='${J([e.id])}'>Correct</button><button class="mini" data-dec="no" data-ids='${J([e.id])}'>Wrong</button></span></div>`).join("")}</div>
    </div>`;
  }).join("");
  const singleHtml = single.map((e) => `<div class="rv">
      <h4><span>${esc(what(e))}${area(e)}</span>${e.polygon ? `<button class="link" data-goto='${J([e.id])}'>Show</button>` : ""}</h4>
      <ul>${e.flags.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      ${e.kind === "room" || e.kind === "other" ? labelChips([e.id]) :
        `<div class="acts"><button class="btn" data-dec="ok" data-ids='${J([e.id])}'>Correct</button></div>`}</div>`).join("");
  $("#review").innerHTML = `
    ${S.b.flags.length ? `<div class="rv"><h4>Drawing</h4><ul>${S.b.flags.map((f) => `<li>${esc(f)}</li>`).join("")}</ul></div>` : ""}
    ${open.length ? "" : `<div class="panel-note">Nothing left to review in this drawing.</div>`}
    ${groupHtml}${singleHtml}
    ${done.length ? `<details class="done"><summary>Reviewed · ${done.length}</summary>${done.map((e) => `<div class="sub-row">
      <button class="link" data-goto='${J([e.id])}'>${esc(what(e))}${area(e)}</button><span class="tag">${esc(e.reviewed.replace("label:", "→ "))}</span></div>`).join("")}</details>` : ""}
    <div class="pane-actions"><button class="btn" data-view-go="rules">${icon("sparkles")}Learned rules · ${RULES.rules.length}</button></div>`;
}

function renderRules() {
  setBadge("#rules-badge", RULES.rules.length);
  $("#rules").innerHTML = RULES.rules.map((r) => `<div class="rule">
      <div class="rule-top"><b>${esc(RULES.labels[r.label] || r.label)}</b>
        <span class="tag ${r.trusted ? "good" : "warn"}">${r.trusted ? "trusted" : "learning"}</span>
        <span class="tag">${r.origin === "seed" ? "starter" : "learned"}</span></div>
      <div class="rule-txt">${esc(r.text)}</div>
      <div class="meter"><i class="${r.trusted ? "ok" : ""}" style="width:${Math.round(r.confidence * 100)}%"></i></div>
      <div class="rule-txt">${Math.round(r.confidence * 100)}% · confirmed on ${r.n_drawings} of 3 drawings · ${r.rejected} rejected
        · <button class="link del" data-delrule="${esc(r.id)}">delete</button></div></div>`).join("") +
    `<div class="panel-note">Labelling an element teaches a rule from what can be measured: name or number, fixtures inside, area.
      Rules apply to every drawing. A rule is trusted at 90% with confirmations on 3 different drawings; after that its matches
      skip review. Marking a match wrong lowers it.</div>`;
}

async function sendReview(ids, decision, label) {
  const r = await fetch("/api/review", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: S.path, ids, decision, label }) });
  const res = await r.json();
  if (!r.ok) { toast(res.detail || "Could not save"); return; }
  toast(res.learned === "saved" ? "Saved" : res.learned);
  await refreshBuilding();
}
async function refreshBuilding() {
  const [b] = await Promise.all([(await fetch(`/api/building?path=${encodeURIComponent(S.path)}`)).json(), loadRules()]);
  S.b = b;
  S.index = Object.fromEntries(b.elements.map((e) => [e.id, e]));
  drawPlan(false); renderAll();
  if (S.three && !$("#three-view").classList.contains("hidden")) S.three.load(S.b, S.bg, Number($("#height").value));
}
function toast(msg) {
  const t = document.createElement("div");
  t.className = "toast"; t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 6000);
}
function onReviewClick(e) {
  const t = e.target.closest("button");
  if (!t) return;
  if (t.dataset.viewGo) setView(t.dataset.viewGo);
  if (t.dataset.goto) { const ids = JSON.parse(t.dataset.goto); setView("plan"); highlight(ids, true); if (ids.length === 1) select(ids[0]); }
  if (t.dataset.expand) $(`#sub-${CSS.escape(t.dataset.expand)}`).classList.toggle("hidden");
  if (t.dataset.dec) sendReview(JSON.parse(t.dataset.ids), t.dataset.dec);
  if (t.dataset.label) {
    let label = t.dataset.label;
    if (label === "?") label = prompt("What is it? (e.g. storage, technical room, sauna)");
    if (label) sendReview(JSON.parse(t.dataset.ids), "label", label);
  }
  if (t.dataset.delrule && confirm("Delete this rule? Elements it classified go back to review.")) {
    fetch(`/api/rules/${encodeURIComponent(t.dataset.delrule)}`, { method: "DELETE" }).then(refreshBuilding);
  }
}
$("#review").addEventListener("click", onReviewClick);
$("#rules").addEventListener("click", onReviewClick);

// ---------- boot ----------
loadProjects().then(() => {
  const first = S.projects.find((p) => p.group.startsWith("Swiss"));
  if (first) openProject(first.path);
});
