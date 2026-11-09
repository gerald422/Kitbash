"""Chest inserts through TIOW Inbox 1.17.8 (sent like the Squad Builder does): Josh's own insert lands exactly where he
put it in Desktop\\for inserts.blend, a few others from each set land on the same spot, touching the torso and cutting
in no deeper than his; a torso without the spot leaves the insert off it.
python t_inserts.py -- TESTLIB TIOW_FILE OUTDIR JOSH_DIR (JOSH_DIR: the blend's torso_M.npy / insert_M.npy / insert.npy)"""
import bpy, json, os, sys, tempfile
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W, TIOW, OUTD, JD = sys.argv[sys.argv.index("--") + 1:][:4]
sys.path.insert(0, "/home/claude/kitbash/tests"); import rend
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
MF = "MarFil/"; IN = "Inserts/Bits Inserts - "
TOR = MF + "MarFil Assault - Torso 2 Insert"
BODY = [(MF + "MarFil Assault - Legs 1A", "Legs", "Waist"), (MF + "MarFil Assault - Arm 1A R", "Arms", "Shoulder R"),
        (MF + "mk5 helmet v1", "Heads", "Neck")]
MODELS = {"josh": [(TOR, "Chests", None)] + BODY + [(IN + "HH GEN3 02", "Chest Inserts", "Chest Insert")]}
for k, n in enumerate(["Anvils of Barbarus 06", "Iron Gorgon 01", "Crimson-Sand 09", "Crimson-Sand Clear 04", "HH GEN3 08"]):
    MODELS["i%d" % k] = [(TOR, "Chests", None), BODY[0], (IN + n, "Chest Inserts", "Chest Insert")]
MODELS["no_spot"] = [(MF + "MarFil Assault - Torso 1", "Chests", None), BODY[0], (IN + "HH GEN3 02", "Chest Inserts", "Chest Insert")]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True); bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
ck("TIOW Inbox is 1.17.8", T.bl_info["version"] == (1, 17, 8), T.bl_info["version"])
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox(); n = 0
for i, (m, parts) in enumerate(MODELS.items()):
    for p, cat, sock in parts:
        r = {"schemaVersion": 1, "path": W + "/" + p + ".stl", "name": os.path.basename(p), "title": "", "category": cat, "tags": [],
             "itemId": "", "sentAt": "", "model": m}
        if sock: r["socket"] = sock
        else: r["at"] = [40 * i, 0, 0]
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
def find(m, p):
    return next((x for x in obs if x.get("tiow_model") == m and os.path.basename(x.get("tiow_src", "")) == os.path.basename(p) + ".stl"), None)
def bvh(o):
    return BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [p.vertices[:] for p in o.data.polygons])
D3 = [Vector(d).normalized() for d in ((0.0123, 0.0177, 1), (1, 0.031, -0.017), (-0.023, -1, 0.041))]
def odd(t, v, d):
    k = 0; q = v.copy()
    for _ in range(12):
        h = t.ray_cast(q, d, 500)
        if h[0] is None: break
        k += 1; q = h[0] + d * 1e-4
    return k % 2
def close_deep(o, host):
    t = bvh(host); V = [o.matrix_world @ v.co for v in o.data.vertices][::max(1, len(o.data.vertices) // 3000)]
    close, deep = 9e9, 0.0
    for v in V:
        d = t.find_nearest(v)[3]; close = min(close, d)
        if d > deep and d < 3 and all(odd(t, v, dd) for dd in D3): deep = d
    return close, deep

# 1. Josh's insert where he put it: compare relative to the torso, vertex by vertex, with his blend
Mt, Mi, VI = np.load(JD + "/torso_M.npy"), np.load(JD + "/insert_M.npy"), np.load(JD + "/insert.npy")
tor, ins = find("josh", TOR), find("josh", IN + "HH GEN3 02")
ck("josh: every part placed", all(find("josh", p) is not None for p, _, _ in MODELS["josh"]), [o.get("tiow_src") for o in obs if o.get("tiow_model") == "josh"])
if tor and ins:
    Rt = np.linalg.inv(np.array(tor.matrix_world)) @ np.array(ins.matrix_world)
    Vl = np.array([v.co[:] for v in ins.data.vertices])                    # the library file (Josh's scale baked in)
    mine = (np.c_[Vl, np.ones(len(Vl))] @ Rt.T)[:, :3]
    D = np.linalg.norm(Mi[:3, :3], axis=0)
    # his: file = mesh + off; library = file * D  ->  mesh = library / D - off
    VF = Vl / D; off = VF.min(0) - VI.min(0)
    his = (np.c_[VF - off, np.ones(len(VF))] @ (np.linalg.inv(Mt) @ Mi).T)[:, :3]
    dev = float(np.abs(mine - his).max())
    print("      Josh's HH GEN3 02: largest vertex difference from his blend %.4f mm" % dev)
    ck("josh: HH GEN3 02 exactly where Josh put it (<= 0.01 mm)", dev <= 0.01, dev)
    c, d = close_deep(ins, tor); ref_cut = d
    print("      HH GEN3 02 on the torso: closest %.3f, deepest cut %.3f mm (Josh's own placement)" % (c, d))
# 2. the others on the same spot
for m, parts in MODELS.items():
    if not m.startswith("i"):
        continue
    p = parts[-1][0]; o, t = find(m, p), find(m, TOR)
    ck("%s: %s placed" % (m, os.path.basename(p)), o is not None and t is not None)
    if o is None or t is None:
        continue
    c, d = close_deep(o, t)
    print("      %-36s closest %.3f, deepest cut %.3f mm" % (os.path.basename(p), c, d))
    ck("%s: %s touches the torso (<= 0.1 mm)" % (m, os.path.basename(p)), c <= 0.1, c)
    lim = 1.0 if "Iron Gorgon 01" in p else ref_cut + 0.05
    ck("%s: %s cuts in no deeper than Josh's (+0.05 mm; Iron Gorgon 01's back emblem 1.0)" % (m, os.path.basename(p)), d <= lim, d)
# 3. a torso without the spot
o, t = find("no_spot", IN + "HH GEN3 02"), find("no_spot", MF + "MarFil Assault - Torso 1")
if o is not None and t is not None:
    _, d = close_deep(o, t)
    far = (Vector(o.matrix_world.translation) - Vector(t.matrix_world.translation)).length
    print("      on Torso 1 (no spot): insert %s, %.1f mm from the torso's origin, tiow_target %s" % ("imported" if o else "not imported", far, o.get("tiow_target")))
    ck("no_spot: the insert isn't put on a torso without the spot (left in the scene, away from it)", far > 20 and d == 0.0, (far, d))
else:
    print("      on Torso 1 (no spot): insert imported:", o is not None)
os.makedirs(OUTD, exist_ok=True)
sc = bpy.context.scene; rend.setup(sc, 420)
COL = {"Chests": rend.BLUE, "Legs": rend.GREY, "Arms": rend.GREY, "Heads": rend.ORANGE, "Chest Inserts": rend.RED}
for m in MODELS:
    ms = [o for o in obs if o.get("tiow_model") == m]
    rend.render(sc, OUTD, m, ms, {"front": (0.25, 1, 0.2), "right": (1, 0.25, 0.15)}, [COL.get(o.get("tiow_category"), rend.GREY) for o in ms])
print("FAILS:", fails if fails else "none")
