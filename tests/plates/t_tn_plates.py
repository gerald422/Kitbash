"""Turtle Ninja legs with the Mar Fil hip plates and buckle through TIOW Inbox 1.17.7, sent like the Squad Builder does
(model + socket). Each plate / buckle is compared with its seat (tn_seat.py result, the check sheets), point sets in
the legs' file coordinates; the trophy spots are checked against the seat's sockets.
python t_tn_plates.py -- WORKLIB TIOW_FILE SEAT_JSON  (WORKLIB/legs.json: the legs library paths to build)"""
import bpy, json, os, sys, tempfile, struct
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/claude/test"); import rend
W, TIOW, JS = sys.argv[sys.argv.index("--") + 1:][:3]
seat = json.load(open(JS)); LEGS = json.load(open(os.path.join(W, "legs.json")))
M16 = lambda a: np.array(a, float).reshape(4, 4); inv = np.linalg.inv
D = W + "/Mar Fil - Tacticus/AssaultMarines-V2/"
PLATE = D + "Hip Plates/MarFil Assault - Hip Plate L.stl"; BUCKLE = D + "Buckles/MarFil Assault - Buckle.stl"
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
def stl(p):
    d = open(p, "rb").read(); n = struct.unpack("<I", d[80:84])[0]
    return np.frombuffer(d[84:84 + n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))["v"].reshape(-1, 3).astype(float)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
ck("TIOW Inbox 1.17.7", T.bl_info["version"] == (1, 17, 7), T.bl_info["version"])
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox()
n = 0
def send(model, reqs, at):
    global n
    for p, cat, sock in reqs:
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": model}
        if sock: r["socket"] = sock
        if n == 0 or sock is None: r["at"] = at
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
cat = lambda o: o.get("tiow_category")
models = {}
for i, rel in enumerate(LEGS):
    m = "m%d" % i; LP = W + "/" + rel + ".stl"
    # m0 plates first; m1 buckle first; m2 only the right plate (the mirror variant on its own)
    order = [[(PLATE, "Hip Plates", "Plate L"), (PLATE, "Hip Plates", "Plate R"), (BUCKLE, "Buckles", "Buckle")],
             [(BUCKLE, "Buckles", "Buckle"), (PLATE, "Hip Plates", "Plate R"), (PLATE, "Hip Plates", "Plate L")],
             [(PLATE, "Hip Plates", "Plate R"), (BUCKLE, "Buckles", "Buckle")]][i % 3]
    send(m, [(LP, "Legs", None)] + order, [80 * i, 0, 0])
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
for i, rel in enumerate(LEGS):
    m = "m%d" % i; r = seat[rel]; name = rel.rsplit("/", 1)[-1]
    root = [o for o in obs if o.get("tiow_model") == m and o.get("tiow_model_root")][0]
    mine = [o for o in obs if T._model_root(o) is root]
    legs = root; Ml = np.array(legs.matrix_world); s = float(legs.get("tiow_unit", 1.0))
    ck("%s: the legs are the model's root" % name, cat(legs) == "Legs", cat(legs))
    snap = {}
    for o in mine:
        if o.get("ws_snap_type"): snap.setdefault(o["ws_snap_type"], []).append(o)
    print(m, name, sorted((k, [o.name for o in v]) for k, v in snap.items()))
    for st, key, src in (("Plate L", "L", PLATE), ("Plate R", "R", PLATE), ("Buckle", "B", BUCKLE)):
        if i % 3 == 2 and st == "Plate L": continue
        got = snap.get(st, [])
        ck("%s: one part on %s" % (name, st), len(got) == 1, [o.name for o in got])
        for o in got:
            me = o.data; v = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", v); V = v.reshape(-1, 3)
            Mo = inv(Ml) @ np.array(o.matrix_world); P = (V @ Mo[:3, :3].T + Mo[:3, 3]) / s
            E = M16(r["parts"][key]); Q = stl(src) @ E[:3, :3].T + E[:3, 3]
            d = cKDTree(Q).query(P[::5])[0]
            ck("%s %-8s %-28s within %.3f mm of its seat (95%% %.3f)" % (name, st, o.name, d.max(), np.percentile(d, 95)), d.max() < 0.05, d.max())
    # the trophy spots: the legs' own sockets (empties) match the seat
    for t in ("Trophy R", "Trophy L"):
        es = [c for c in legs.children if c.type == 'EMPTY' and c.get("ws_type", c.get("type")) == t] or \
             [c for c in bpy.data.objects if c.parent is legs and t in c.name]
        if not es:
            ck("%s: %s socket on the legs" % (name, t), False, [c.name for c in legs.children][:12]); continue
        Me = inv(Ml) @ np.array(es[0].matrix_world); Me[:3, 3] /= s
        E = M16(r["sockets"][t]); dd = np.linalg.norm(Me[:3, 3] - E[:3, 3])
        ck("%s: %s socket where seated (%.3f mm)" % (name, t, dd), dd < 0.01, dd)
    models[m] = mine
scene = bpy.context.scene; rend.setup(scene, 600)
COL = {"Hip Plates": rend.BLUE, "Buckles": (0.6, 0.45, 0.85, 1)}
for m in models:
    ob = models[m]
    rend.render(scene, "/home/claude/work/tlib_out", "tn_" + m, ob, {"front": (0, 1, 0.2), "left": (-1, 0.1, 0.15), "right": (1, 0.1, 0.15)},
                [COL.get(cat(o), rend.GREY) for o in ob], pad=1.05)
print("fails:", len(fails))
