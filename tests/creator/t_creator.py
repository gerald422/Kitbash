"""add_creator.py's Blender check (from tests/wg/t_wg.py): Mar Fil Assault marines built by TIOW Inbox the way the
Squad Builder sends them, wearing the new maker's parts. Every requested part must snap; each new part must touch its
host (closest <= 0.5 mm) and cut in no deeper than 0.65 mm (inside = three rays agree, so an open helmet neck or pad
shell isn't read as a cut). Renders each model front and right into one sheet.
    /home/claude/bpyenv/bin/python t_creator.py -- JOB.json
JOB: {"worklib", "tiow", "out", "new": "NEW/", "models": {name: [[path in worklib without .stl, category, socket], ...]}}
Writes OUT/results.json and OUT/test.jpg."""
import bpy, json, os, sys, tempfile
from mathutils import Vector
from mathutils.bvhtree import BVHTree
J = json.load(open(sys.argv[sys.argv.index("--") + 1]))
W, TIOW, OUTD, NEW, MODELS = J["worklib"], J["tiow"], J["out"], J.get("new", "NEW/"), J["models"]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")); import rend
fails, res = [], []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True); bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox(); n = 0
for i, (m, parts) in enumerate(MODELS.items()):
    for p, cat, sock in parts:
        r = {"schemaVersion": 1, "path": W + "/" + p + ".stl", "name": os.path.basename(p), "title": "", "category": cat,
             "tags": [], "itemId": "", "sentAt": "", "model": m}
        if sock: r["socket"] = sock
        else: r["at"] = [80 * i, 0, 0]
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
D3 = [Vector(d).normalized() for d in ((0.0123, 0.0177, 1), (1, 0.031, -0.017), (-0.023, -1, 0.041))]
def bvh(o): return BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [p.vertices[:] for p in o.data.polygons])
def odd(t, v, d):
    k = 0; q = v.copy()
    for _ in range(12):
        h = t.ray_cast(q, d, 500)
        if h[0] is None: break
        k += 1; q = h[0] + d * 1e-4
    return k % 2
def inside_depth(o, others):
    trees = [bvh(x) for x in others]; V = [o.matrix_world @ v.co for v in o.data.vertices][::max(1, len(o.data.vertices) // 1500)]
    close = min(min((t.find_nearest(v)[3] or 9e9) for t in trees) for v in V); deep = 0.0
    for v in V:
        for t in trees:
            if all(odd(t, v, d) for d in D3): deep = max(deep, t.find_nearest(v)[3])
    return close, deep
for m, parts in MODELS.items():
    mine = [o for o in obs if o.get("tiow_model") == m]
    for p, cat, sock in parts:
        o = next((x for x in mine if os.path.basename(x.get("tiow_src", "")).startswith(os.path.basename(p))), None)
        ck("%s: %s placed%s" % (m, os.path.basename(p), (" on " + sock) if sock else ""), o is not None)
        if o is None or not sock or not p.startswith(NEW): continue
        close, deep = inside_depth(o, [x for x in mine if x is not o])
        res.append({"model": m, "part": os.path.basename(p), "socket": sock, "closest": round(close, 3), "cut": round(deep, 3)})
        print("      %-40s closest %.2f mm, deepest cut %.2f mm" % (os.path.basename(p)[:40], close, deep))
        ck("%s: %s touches (closest <= 0.5 mm)" % (m, os.path.basename(p)), close <= 0.5, close)
        ck("%s: %s cuts in <= 0.65 mm" % (m, os.path.basename(p)), deep <= 0.65, deep)
os.makedirs(OUTD, exist_ok=True)
sc = bpy.context.scene; rend.setup(sc, 420)
COL = {"Chests": rend.BLUE, "Shoulder Pads": rend.PURPLE, "Heads": rend.ORANGE, "Backpacks": rend.GREEN}
tiles = []
for m in MODELS:
    ms = [o for o in obs if o.get("tiow_model") == m]
    newb = tuple(os.path.basename(p) for p, _, _ in MODELS[m] if p.startswith(NEW))
    cols = [COL.get(o.get("tiow_category"), rend.RED) if newb and os.path.basename(o.get("tiow_src", "")).startswith(newb)
            else (rend.BLUE if o.get("tiow_category") == "Chests" else rend.GREY) for o in ms]
    f = rend.render(sc, OUTD, m, ms, {"front": (0.35, 1, 0.25), "right": (1, 0.2, 0.15)}, cols); tiles.append((m, f))
from PIL import Image, ImageDraw
w = 420; sheet = Image.new("RGB", (2 * w, len(tiles) * (w + 20)), (255, 255, 255)); d = ImageDraw.Draw(sheet)
for r, (m, f) in enumerate(tiles):
    for c, v in enumerate(("front", "right")):
        sheet.paste(Image.open(f[v]).convert("RGB"), (c * w, r * (w + 20) + 20)); os.remove(f[v])
    d.text((6, r * (w + 20) + 4), m + ": " + ", ".join(os.path.basename(p) for p, _, _ in MODELS[m] if p.startswith(NEW)), fill=(0, 0, 0))
sheet.save(os.path.join(OUTD, "test.jpg"), quality=85)
json.dump({"fails": fails, "parts": res}, open(os.path.join(OUTD, "results.json"), "w"), indent=1)
print("FAILS:", fails if fails else "none")
