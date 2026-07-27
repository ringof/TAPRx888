#!/usr/bin/env python3
"""Wrap the mechanical-assembly GLB in a self-contained interactive HTML viewer.

Renders the assembly with a small pinned three.js (r148) so the four top-level
parts -- enclosure, main board, front end plate, rear end plate -- can be toggled
on and off with checkboxes. Everything (three.js core + GLTFLoader + OrbitControls
+ RoomEnvironment, and the base64 GLB) is embedded, so the output is a single
.html file that opens in any browser with no CAD tools and no network. Built by
mechanical-ci and deployed to GitHub Pages.

Why three.js instead of <model-viewer>: model-viewer has no public per-node
visibility API, and the parts we want to toggle are already separate, prefixed
nodes in the GLB (assemble_glb.py names them "<part>_<i>"). three.js exposes the
scene graph directly, so a checkbox just flips `object.visible` on every node
whose name starts with the part key.

Inlining without a build step: the three.js core and the three addons ship as ES
modules; the addons import only from the bare specifier 'three'. We embed each
source verbatim in a <script type="text/plain"> block, turn it into a Blob URL at
runtime, register an import map that points 'three' at the core's Blob URL, and
dynamically import the addon Blobs. No bundler, no network -- matching the
"curl a prebuilt lib + inline it" approach of the old model-viewer viewer.
"""
import argparse
import base64
import json


# The four top-level parts, in legend order: (node-name prefix, label, swatch).
# The prefixes match the node names assemble_glb.py writes ("<part>_<i>"), so a
# part toggles every mesh whose name starts with its key. Screws and SMA hardware
# are baked into the enclosure GLB, so they ride with "enclosure".
PARTS = [
    ("enclosure",      "Enclosure",        "#9ea3a6"),
    ("main-board",     "Main board",       "#1e4488"),
    ("endplate-front", "Front end plate",  "#1e4488"),
    ("endplate-rear",  "Rear end plate",   "#1e4488"),
]


def _lib_block(el_id, path):
    """Embed a JS source file as inert raw text we can Blob-ify at runtime.

    <script type="text/plain"> content is raw text (not executed), which sidesteps
    all quoting: three.js shaders use backtick template literals, so wrapping the
    source in a JS string is not an option. A literal </script would end the block
    early; neutralise it defensively (none of the pinned r148 files contain it)."""
    src = open(path, encoding="utf-8").read().replace("</script", "<\\/script")
    return '<script type="text/plain" id="%s">%s</script>' % (el_id, src)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--glb", required=True)
    ap.add_argument("--three", required=True, help="three.module.js (r148)")
    ap.add_argument("--gltf", required=True, help="jsm/loaders/GLTFLoader.js")
    ap.add_argument("--orbit", required=True, help="jsm/controls/OrbitControls.js")
    ap.add_argument("--room", required=True, help="jsm/environments/RoomEnvironment.js")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rev", default="", help="short git sha for the header")
    a = ap.parse_args()

    glb_b64 = base64.b64encode(open(a.glb, "rb").read()).decode("ascii")
    libs = "\n".join([
        _lib_block("lib-three", a.three),
        _lib_block("lib-gltf", a.gltf),
        _lib_block("lib-orbit", a.orbit),
        _lib_block("lib-room", a.room),
    ])
    rev = (" &middot; " + a.rev) if a.rev else ""
    parts_js = json.dumps([[k, l, s] for k, l, s in PARTS])

    # Toggle panel: one checkbox per part (checked = visible). data-part carries
    # the node-name prefix the viewer script buckets on.
    toggles = "\n".join(
        '    <label><input type="checkbox" data-part="%s" checked>'
        '<b style="background:%s"></b>%s</label>' % (key, swatch, label)
        for key, label, swatch in PARTS)

    doc = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TAPRX-888 - mechanical fit-check</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  html, body {{ height:100%; }}
  body {{ margin:0; font-family: system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
    background:#14171a; color:#e7ebee; display:flex; flex-direction:column; }}
  header {{ padding:14px 20px; border-bottom:1px solid #2a3037; flex:0 0 auto; }}
  h1 {{ margin:0; font-size:17px; font-weight:620; letter-spacing:-.01em; }}
  header p {{ margin:4px 0 0; font-size:12.5px; color:#98a1a7; }}
  /* the viewport fills the remaining height; min-height:0 lets the flex child
     actually shrink/grow instead of collapsing to its default size */
  .wrap {{ position:relative; flex:1 1 auto; min-height:0;
    background: radial-gradient(120% 120% at 50% 25%, #20262c 0%, #101315 70%); }}
  canvas {{ position:absolute; inset:0; width:100%; height:100%; display:block; }}
  .panel {{ position:absolute; left:16px; bottom:14px; display:flex;
    flex-direction:column; gap:7px; font-size:12px; background:rgba(20,23,26,.72);
    padding:10px 13px; border:1px solid #2a3037; border-radius:9px;
    backdrop-filter:blur(3px); }}
  .panel .head {{ font-size:11px; text-transform:uppercase; letter-spacing:.06em;
    color:#8b939a; margin-bottom:1px; }}
  .panel label {{ display:flex; align-items:center; gap:7px; cursor:pointer;
    user-select:none; }}
  .panel input {{ margin:0; cursor:pointer; accent-color:#3b6fd4; }}
  .panel b {{ display:inline-block; width:11px; height:11px; border-radius:3px; }}
  .hint {{ position:absolute; right:16px; bottom:14px; font-size:11.5px;
    color:#8b939a; background:rgba(20,23,26,.72); padding:6px 10px;
    border:1px solid #2a3037; border-radius:9px; }}
</style>
</head><body>
<header>
  <h1>TAPRX-888 &mdash; mechanical fit-check</h1>
  <p>Enclosure &middot; main board &middot; front / rear end plates{rev}. Drag to orbit, scroll to zoom, toggle parts at left.</p>
</header>
<div class="wrap">
  <canvas id="view"></canvas>
  <div class="panel">
    <span class="head">Show parts</span>
{toggles}
  </div>
  <div class="hint">no CAD tool needed &middot; opens offline</div>
</div>

{libs}
<script type="text/plain" id="glb-b64">{glb_b64}</script>

<script>
// Turn each embedded source into a Blob URL, wire 'three' through an import map,
// then dynamically import the core + addons (which import only 'three'). The
// import map must be registered before the first module load, which it is.
(async function () {{
  const raw  = id => document.getElementById(id).textContent;
  const blob = txt => URL.createObjectURL(new Blob([txt], {{ type: "text/javascript" }}));

  const threeUrl = blob(raw("lib-three"));
  const map = document.createElement("script");
  map.type = "importmap";
  map.textContent = JSON.stringify({{ imports: {{ three: threeUrl }} }});
  document.head.appendChild(map);

  const THREE = await import(threeUrl);
  const {{ GLTFLoader }}    = await import(blob(raw("lib-gltf")));
  const {{ OrbitControls }} = await import(blob(raw("lib-orbit")));
  const {{ RoomEnvironment }} = await import(blob(raw("lib-room")));

  const canvas = document.getElementById("view");
  const wrap = canvas.parentElement;

  const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;

  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  const key = new THREE.DirectionalLight(0xffffff, 1.15);
  key.position.set(1, 1.6, 1.2);
  scene.add(key);
  scene.add(new THREE.AmbientLight(0xffffff, 0.12));  // faint fill; env does most of it

  function resize() {{
    const w = wrap.clientWidth, h = wrap.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(h, 1);
    camera.updateProjectionMatrix();
  }}
  window.addEventListener("resize", resize);

  // Decode the base64 GLB to an ArrayBuffer and parse it in-place.
  const bin = atob(raw("glb-b64").trim());
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);

  const PARTS = {parts_js};  // [prefix, label, swatch] rows, mirrors the checkboxes

  new GLTFLoader().parse(bytes.buffer, "", (gltf) => {{
    const root = gltf.scene;
    scene.add(root);

    // Bucket every node under its part by name prefix (assemble_glb.py names them
    // "<part>_<i>"); a checkbox flips `visible` on its bucket.
    const buckets = {{}};
    for (const [k] of PARTS) buckets[k] = [];
    root.traverse((o) => {{
      if (!o.name) return;
      for (const [k] of PARTS) if (o.name.startsWith(k)) {{ buckets[k].push(o); break; }}
    }});

    // Centre the assembly at the origin and frame it (assembly is Y-up already).
    const box = new THREE.Box3().setFromObject(root);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    root.position.sub(center);

    const maxDim = Math.max(size.x, size.y, size.z);
    const dist = maxDim / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
    camera.position.set(dist * 0.85, dist * 0.62, dist * 1.05);  // 3/4 view
    camera.near = maxDim / 100;
    camera.far = maxDim * 100;
    camera.updateProjectionMatrix();
    controls.target.set(0, 0, 0);
    controls.update();

    document.querySelectorAll(".panel input[data-part]").forEach((cb) => {{
      cb.addEventListener("change", () => {{
        for (const o of buckets[cb.dataset.part] || []) o.visible = cb.checked;
      }});
    }});

    resize();
    // Test/debug hook: lets a headless browser inspect the scene + toggle state.
    window.__viewer = {{ THREE, scene, root, buckets, camera, controls }};
  }}, (err) => {{
    console.error("GLB parse failed", err);
    document.querySelector(".hint").textContent = "failed to load model";
  }});

  (function loop() {{
    requestAnimationFrame(loop);
    controls.update();
    renderer.render(scene, camera);
  }})();
  resize();
}})();
</script>
</body></html>"""

    with open(a.out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("wrote", a.out, len(doc), "bytes")


if __name__ == "__main__":
    main()
