// 3D view: extrudes the extracted 2D model. Heights are not in the drawings, so they are a stated assumption.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const ROOM_COLORS = { bathroom: 0x27a9c9, wc: 0x27a9c9, kitchen: 0xd8b36a, bedroom: 0x4a5b5e, balcony: 0x2c3739, sauna: 0xe4693f, storage: 0x56666a, corridor: 0x3a4749 };
const WET = /bad|wc|dusche|douche|bagno|salle de bain|kph|pesu|sauna|bath|toilet/i;

export function create(container, onPick) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  container.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 5000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8a8a, 2.2));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6);
  sun.position.set(30, 60, 20);
  scene.add(sun);
  const root = new THREE.Group();
  scene.add(root);
  let meshes = [];
  const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();

  function resize() {
    const r = container.getBoundingClientRect();
    if (!r.width) return;
    renderer.setSize(r.width, r.height);
    camera.aspect = r.width / r.height;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(container);
  renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });

  let down = null;
  renderer.domElement.addEventListener("pointerdown", (e) => (down = [e.clientX, e.clientY]));
  renderer.domElement.addEventListener("pointerup", (e) => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;
    const r = renderer.domElement.getBoundingClientRect();
    mouse.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(meshes.filter((m) => m.userData.id), false)[0];
    onPick(hit ? hit.object.userData.id : null);
  });

  function clear() {
    root.traverse((o) => { o.geometry?.dispose(); o.material?.dispose?.(); });
    root.clear();
    meshes = [];
  }

  function load(b, bg, height) {
    clear();
    const raster = b.source_type === "raster";
    let s = 1;
    if (raster) {
      const w = b.view.image_size?.[0] || 1000;
      s = 30 / w; // not to scale: normalised so the sheet is 30 units wide
    }
    const P = (p) => (raster ? [p[0] * s, -p[1] * s] : [p[0], p[1]]);
    const levels = b.levels.length ? b.levels : [null];
    const lvOff = (lv) => Math.max(0, levels.indexOf(lv)) * (height + 0.4);

    function shape(poly) {
      const sh = new THREE.Shape();
      poly.forEach((p, i) => { const [x, y] = P(p); i ? sh.lineTo(x, y) : sh.moveTo(x, y); });
      return sh;
    }
    function prism(poly, z0, z1, mat, id) {
      if (!poly || poly.length < 3) return;
      const g = new THREE.ExtrudeGeometry(shape(poly), { depth: z1 - z0, bevelEnabled: false });
      g.rotateX(-Math.PI / 2);
      g.translate(0, z0, 0);
      const m = new THREE.Mesh(g, mat.clone());
      m.userData = { id, base: m.material.color.getHex() };
      root.add(m);
      meshes.push(m);
      return m;
    }
    const mat = (color, opacity = 1) => new THREE.MeshStandardMaterial({ color, roughness: 0.85, transparent: opacity < 1, opacity, depthWrite: opacity >= 1 });
    const floors = b.source_type === "ifc";

    for (const e of b.elements) {
      if (!e.polygon || e.polygon.length < 3) continue;
      const z = floors ? lvOff(e.level) : 0;
      if (e.kind === "room") {
        const wet = WET.test(e.name || "") || ["bathroom", "wc", "sauna"].includes(e.subtype);
        const c = ROOM_COLORS[e.subtype] ?? (wet ? 0x27a9c9 : e.outdoor ? 0x2c3739 : 0x46575a);
        prism(e.polygon, z, z + 0.06, mat(c), e.id);
        if (!bg?.walls?.length) { // no wall geometry: show the room as a light volume with edges
          const v = prism(e.polygon, z + 0.06, z + height, mat(0x8a999b, 0.08));
          if (v) { v.userData = {}; const ed = new THREE.LineSegments(new THREE.EdgesGeometry(v.geometry, 30), new THREE.LineBasicMaterial({ color: 0x5f6e70 })); root.add(ed); }
        }
      } else if (e.kind === "door") prism(e.polygon, z, z + Math.min(2.1, height), mat(0xe4693f, 0.9), e.id);
      else if (e.kind === "window") prism(e.polygon, z + 0.9, z + Math.min(2.1, height), mat(0x8fdcef, 0.55), e.id);
      else if (e.kind === "fixture") prism(e.polygon, z, z + (e.subtype === "sauna_stove" ? 0.8 : 0.45), mat(0xd8b36a), e.id);
    }
    for (const w of bg?.walls || []) prism(w, 0, height, mat(0xc9d2d2));

    // frame the model
    const box = new THREE.Box3().setFromObject(root);
    const c = box.getCenter(new THREE.Vector3()), size = box.getSize(new THREE.Vector3()).length() || 10;
    controls.target.copy(c);
    camera.position.set(c.x + size * 0.45, c.y + size * 0.65, c.z + size * 0.6);
    camera.near = size / 1000; camera.far = size * 20; camera.updateProjectionMatrix();
    resize();
  }

  function highlight(ids) {
    for (const m of meshes) {
      if (!m.userData.id) continue;
      m.material.color.setHex(ids.has(m.userData.id) ? 0xf2d16b : m.userData.base);
      m.material.emissive?.setHex(ids.has(m.userData.id) ? 0x5a4500 : 0x000000);
    }
  }
  return { load, highlight, resize };
}
