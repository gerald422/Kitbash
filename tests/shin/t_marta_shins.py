"""Marta legs with shin pads through TIOW Inbox 1.17.7, sent like the Squad Builder (model + socket): each pad must land
on the legs' Shin R/L socket by its fit (point sets in the legs' file coordinates); on legs Josh placed by eye the pad
must also match his placement (placed.json).  python t_marta_shins.py -- WORKLIB TIOW_FILE PLACED_JSON
WORKLIB/test.json: [[legs library path, {"R": pad path, "L": pad path}], ...]"""
import bpy, json, os, sys, tempfile, struct
import numpy as np
W, TIOW, PJ = sys.argv[sys.argv.index("--") + 1:][:3]
TEST = json.load(open(os.path.join(W, "test.json"))); placed = json.load(open(PJ))
M16 = lambda a: np.array(a, float).reshape(4, 4); inv = np.linalg.inv
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
def stl(p):
    d = open(p, "rb").read(); n = struct.unpack("<I", d[80:84])[0]
    return np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))["v"].reshape(-1, 3).astype(float)
tf = lambda M, P: P @ M[:3, :3].T + M[:3, 3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True); bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
ck("TIOW Inbox 1.17.7", T.bl_info["version"] == (1, 17, 7), T.bl_info["version"])
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox(); n = 0
def send(model, reqs, at):
    global n
    for p, cat, sock in reqs:
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": model}
        if sock: r["socket"] = sock
        else: r["at"] = at
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
for i, (rel, pads) in enumerate(TEST):
    send("m%d" % i, [(W + "/" + rel + ".stl", "Legs", None)] + [(W + "/" + pads[s] + ".stl", "Knee Pads", "Shin " + s) for s in "RL"], [80 * i, 0, 0])
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
for i, (rel, pads) in enumerate(TEST):
    m = "m%d" % i; name = rel.rsplit("/", 1)[-1]
    root = [o for o in obs if o.get("tiow_model") == m and o.get("tiow_model_root")][0]; mine = [o for o in obs if T._model_root(o) is root]
    sk = json.load(open(W + "/" + rel + ".sockets.json", encoding="utf-8-sig")); socks = {s["type"]: M16(s["matrix"]) for s in sk["sockets"]}
    Ml = np.array(root.matrix_world); u = float(root.get("tiow_unit", 1.0))
    for s in "RL":
        got = [o for o in mine if o.get("ws_snap_type") == "Shin " + s]
        ck("%s: one pad on Shin %s" % (name, s), len(got) == 1, [o.name for o in got])
        if not got: continue
        o = got[0]; P = stl(W + "/" + pads[s] + ".stl")
        A = inv(Ml) @ np.array(o.matrix_world); A[:3, 3] /= u                     # pad file -> legs file (TIOW scales translations by its unit)
        fit = M16(json.load(open(W + "/" + pads[s] + ".sockets.json", encoding="utf-8-sig"))["fits"]["Shin " + s])
        want = socks["Shin " + s] @ fit
        d = np.linalg.norm(tf(A, P) - tf(want, P), axis=1)
        ck("%s Shin %s: %s on the socket by its fit within %.3f mm (95%% %.3f)" % (name, s, os.path.basename(pads[s]), d.max(), np.percentile(d, 95)), d.max() < 0.05, d.max())
        key = "%s|%s" % (name, s)
        if key in placed:
            e = np.linalg.norm(tf(A, P) - tf(M16(placed[key]["pad_in_legs"]), P), axis=1)
            ck("%s Shin %s: where Josh placed it, within %.3f mm" % (name, s, e.max()), e.max() < 0.05, e.max())
print("FAILED: %d" % len(fails) if fails else "all ok")
