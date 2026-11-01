"""Blade wings through TIOW Inbox 1.17.5 on the TN Mk6 Universal pack: each wing brings its connector onto that side's
Wing Mount and hangs from the connector; the left wing arrives as the mirrored left. Compared with Josh's marine in
base_jumpack.blend (points in the pack's own coordinates, from josh_points.py).
python t_wings.py -- WORKLIB TIOW_FILE JOSH_NPZ"""
import bpy, json, os, sys, tempfile
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/claude/test"); import rend
W, TIOW, JN = sys.argv[sys.argv.index("--") + 1:][:3]
TOR = W + "/Turtle Ninja - Heresy/Mk7-8 Builder/Mk7-8/Chests/TN Mk7-8 - Upper B1.stl"
LEGS = W + "/Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 4B.stl"
PACK = W + "/Turtle Ninja - Heresy/Mk6 Assault Addon 1/Powerpacks/Jump Packs/TN Mk6 Assault - Jump Pack Universal.stl"
WING = W + "/Bits/Bladecrow Jump Packs/Wings/Bits Bladecrow - %s R.stl"
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
ck("TIOW Inbox 1.17.5", T.bl_info["version"] == (1, 17, 5), T.bl_info["version"])
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox()
n = 0
def send(model, reqs, at=None):
    global n
    for p, cat, sock in reqs:
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": model}
        if sock: r["socket"] = sock
        if cat == "Chests": r["at"] = at or [0, 0, 0]
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
send("m1", [(TOR, "Chests", None), (LEGS, "Legs", None), (PACK, "Jump Packs", "Back"),
            (WING % "Wing 01 Open", "Wings", "Wing R"), (WING % "Wing 03 Upwards", "Wings", "Wing L")])
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
mine = lambda c: [o for o in obs if o.get("tiow_category") == c]
pack = mine("Jump Packs")[0]
ck("pack carries Wing Mount L/R, Mechadendrite L/R, Back Top", {"Wing Mount L", "Wing Mount R", "Mechadendrite L", "Mechadendrite R", "Back Top"} <= {c.get("ws_type") for c in pack.children})
mounts = mine("Wing Mounts"); wings = mine("Wings")
ck("two connectors came with the wings", len(mounts) == 2, [o.name for o in mounts])
snap = {o.get("ws_snap_type"): o for o in mounts + wings}
ck("connectors on Wing Mount R and L", "Wing Mount R" in snap and "Wing Mount L" in snap, list(snap))
ck("wings on Wing R and Wing L", "Wing R" in snap and "Wing L" in snap, list(snap))
if "Wing L" in snap:
    wl = snap["Wing L"]
    ck("the left wing is the file's mirrored left (variant 0, %s)" % wl.name, wl.get("tiow_variant") == 0 and wl.name.endswith(" L"), (wl.get("tiow_variant"), wl.name))
for k in ("Wing R", "Wing L", "Wing Mount R", "Wing Mount L"):
    if k in snap:
        host = T._snap_of(snap[k])[0].parent
        ck("%s hangs from %s" % (k, host.get("tiow_category")), host.get("tiow_category") == ("Jump Packs" if "Mount" in k else "Wing Mounts"), host.name)
# against Josh's marine, in the pack's coordinates
J = np.load(JN)
Pi = np.linalg.inv(np.array(pack.matrix_world))
def pts(o):
    a = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", a); V = a.reshape(-1, 3)
    M = Pi @ np.array(o.matrix_world); return V @ M[:3, :3].T + M[:3, 3]
for key, k in (("wingR", "Wing R"), ("wingL", "Wing L"), ("mountR", "Wing Mount R"), ("mountL", "Wing Mount L")):
    if k not in snap: continue
    A = pts(snap[k]); B = J[key]
    d = cKDTree(B).query(A[::7])[0]
    ext = np.linalg.norm(A - A.mean(0), axis=1).max()
    ck("%-13s vs Josh's: median %.2f mm, 95%% %.2f mm, worst %.2f mm (part reaches %.0f mm)" % (k, np.median(d), np.percentile(d, 95), d.max(), ext),
       np.percentile(d, 95) < (1.0 if "Mount" in k else 3.0), (np.median(d), d.max()))
# sending another right wing swaps it and keeps the connector
send("m1", [(WING % "Wing 02 Closed", "Wings", "Wing R")])
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
ws = [o for o in obs if o.get("tiow_category") == "Wings"]; ms = [o for o in obs if o.get("tiow_category") == "Wing Mounts"]
ck("a second right wing replaces the first, the connector stays", len(ws) == 2 and len(ms) == 2 and any("Closed" in o.name for o in ws), ([o.name for o in ws], len(ms)))
scene = bpy.context.scene; rend.setup(scene, 520)
cols = [rend.ORANGE if o.get("tiow_category") == "Wings" else rend.BLUE if o.get("tiow_category") == "Wing Mounts" else rend.GREY for o in obs]
rend.render(scene, "/home/claude/twoarm/wings/out", "tiow_wings", obs, {"back": (0.3, -1, 0.3), "side": (1, -0.3, 0.2)}, cols, pad=1.05)
print("fails:", len(fails))
