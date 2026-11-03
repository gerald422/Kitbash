"""Hip plates, buckle, sheaths, tabards and trophies through TIOW Inbox 1.17.6 on Mar Fil Assault legs, sent like the
Squad Builder does (model + socket). Each part is compared with where Josh checked it (marfil_assault_plates.json),
point sets in the legs' file coordinates. Also: a sheath with no plate yet brings its plate, a tabard brings the buckle.
python t_plates.py -- WORKLIB TIOW_FILE JSON"""
import bpy, json, os, sys, tempfile, struct
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/claude/test"); import rend
W, TIOW, JS = sys.argv[sys.argv.index("--") + 1:][:3]
doc = json.load(open(JS)); M16 = lambda a: np.array(a, float).reshape(4, 4); inv = np.linalg.inv
D = W + "/Mar Fil - Tacticus/AssaultMarines-V2/"
TOR = D + "Chests/MarFil Assault - Torso 1.stl"
LEGS = {"4A": D + "Legs(JumpPack)/Legs/MarFil Assault - Legs 4A.stl", "6A": D + "Legs(JumpPack)/Legs/MarFil Assault - Legs 6A.stl",
        "8A": D + "Legs(JumpPack)/Legs/MarFil Assault - Legs 8A.stl", "S2": D + "Legs/MarFil Assault - Legs 2.stl"}
LNAME = {"4A": "MarFil Assault - Legs 4A", "6A": "MarFil Assault - Legs 6A", "8A": "MarFil Assault - Legs 8A", "S2": "MarFil Assault - Legs 2"}
PLATE = D + "Hip Plates/MarFil Assault - Hip Plate L.stl"; BUCKLE = D + "Buckles/MarFil Assault - Buckle.stl"
SHEATH = D + "Holsters/MarFil Assault - Pistol Sheath %d L.stl"
CB = W + "/CyberBrush - Tacticus/Space Bugs Hunters/"
TAB = CB + "Space Bug Hunters Loinclothes/Accessories/CyberBrush Bug Hunters - Loinclothe %d.stl"
TRO = CB + "Space Bug Hunters Belt Decorations/Accessories/CyberBrush Bug Hunters - Belt Decoration %d.stl"
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
ck("TIOW Inbox 1.17.6", T.bl_info["version"] == (1, 17, 6), T.bl_info["version"])
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox()
n = 0
def send(model, reqs, at):
    global n
    for p, cat, sock in reqs:
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": model}
        if sock: r["socket"] = sock
        if cat == "Chests": r["at"] = at
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
A = np.diag([-1.0, 1, 1, 1])
Pc, Sm = M16(doc["plate_frame"]["matrix"]), M16(doc["plate_self_mirror"]["matrix"])
S_wp, SF = M16(doc["holster_socket_on_plate"]["matrix"]), M16(doc["sheath_fit_on_plate_socket"]["matrix"])
ORN = M16(doc["buckle_part"]["sockets"]["Buckle Ornament"]["matrix"]); TABS = M16(doc["buckle_part"]["sockets"]["Tabard"]["matrix"])
def expected(a, what, k):
    """what -> 4x4 from the part's file (unscaled) into the legs' file, as Josh checked it"""
    e = doc["legs"][LNAME[a]]; WL, WR = M16(e["plates"]["L"]["matrix"]), M16(e["plates"]["R"]["matrix"]); BP = M16(e["buckle_part"]["matrix"])
    if what == "plate L": return WL
    if what == "plate R": return WR @ Sm
    if what == "sheath L": return WL @ S_wp @ SF
    if what == "sheath R": return WR @ Sm @ S_wp @ SF
    if what == "buckle": return BP
    if what == "tabard": t = doc["buckle_part"]["tabard_fits"]["CyberBrush Bug Hunters - Loinclothe %d" % k]; return BP @ TABS @ M16(t["matrix"]) @ np.diag([0.9, 0.9, 0.9, 1])
    if what in ("trophy R", "trophy L"):
        return M16(e["belt"]["Belt Front " + what[-1]]["matrix"]) @ M16(doc["trophy_fits"]["CyberBrush Bug Hunters - Belt Decoration %d" % k])
def check(a, legs, ob, what, src, k=0, tol=0.02):
    Ml = np.array(legs.matrix_world); s = float(legs.get("tiow_unit", 1.0))
    me = ob.data; v = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", v); V = v.reshape(-1, 3)
    Mo = np.array(ob.matrix_world); P = (V @ (inv(Ml) @ Mo)[:3, :3].T + (inv(Ml) @ Mo)[:3, 3]) / s       # in the legs' file (mm)
    E = expected(a, what, k); Q = stl(src) @ E[:3, :3].T + E[:3, 3]
    d = cKDTree(Q).query(P[::5])[0]
    ck("%-3s %-9s %-44s within %.3f mm of Josh's (95%% %.3f)" % (a, what, os.path.basename(src)[:-4] + (" [%s]" % ob.name if ob.get("tiow_variant") is not None else ""), d.max(), np.percentile(d, 95)), d.max() < tol, d.max())
cat = lambda o: o.get("tiow_category")
models = {}
# m1: everything sent in order, plates and buckle first
send("m1", [(TOR, "Chests", None), (LEGS["4A"], "Legs", "Waist"), (PLATE, "Hip Plates", "Plate L"), (PLATE, "Hip Plates", "Plate R"),
            (SHEATH % 1, "Plate Accessories", "Plate Hang L"), (SHEATH % 3, "Plate Accessories", "Plate Hang R"),
            (BUCKLE, "Buckles", "Buckle"), (TAB % 1, "Tabards", "Tabard"), (TRO % 1, "Trophies", "Trophy R"), (TRO % 5, "Trophies", "Trophy L")], [0, 0, 0])
# m2 / m3: a sheath and a tabard with nothing to hang from yet (they bring the plate and the buckle)
send("m2", [(TOR, "Chests", None), (LEGS["6A"], "Legs", "Waist"), (SHEATH % 2, "Plate Accessories", "Plate Hang R"), (TAB % 4, "Tabards", "Tabard")], [80, 0, 0])
send("m3", [(TOR, "Chests", None), (LEGS["S2"], "Legs", "Waist"), (SHEATH % 5, "Plate Accessories", "Plate Hang L"), (TAB % 1, "Tabards", "Tabard"), (TRO % 5, "Trophies", "Trophy R")], [160, 0, 0])
send("m4", [(TOR, "Chests", None), (LEGS["8A"], "Legs", "Waist"), (PLATE, "Hip Plates", "Plate R"), (BUCKLE, "Buckles", "Buckle"), (TAB % 4, "Tabards", "Tabard")], [240, 0, 0])
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
for m, a in (("m1", "4A"), ("m2", "6A"), ("m3", "S2"), ("m4", "8A")):
    root = [o for o in obs if o.get("tiow_model") == m and o.get("tiow_model_root")][0]
    mine = [o for o in obs if T._model_root(o) is root]           # brought plates and buckles carry no model id: they hang in its tree
    legs = [o for o in mine if cat(o) == "Legs"][0]
    snap = {}
    for o in mine:
        st = o.get("ws_snap_type")
        if st: snap.setdefault(st, []).append(o)
    print(m, a, sorted((k, [o.name for o in v]) for k, v in snap.items()))
    for st, what, src, k in (("Plate L", "plate L", PLATE, 0), ("Plate R", "plate R", PLATE, 0), ("Plate Hang L", "sheath L", None, 0), ("Plate Hang R", "sheath R", None, 0),
                             ("Buckle", "buckle", BUCKLE, 0), ("Tabard", "tabard", None, 0), ("Trophy R", "trophy R", None, 0), ("Trophy L", "trophy L", None, 0)):
        for o in snap.get(st, []):
            s_ = str(o.get("tiow_src")); kk = int(s_.rsplit(" ", 1)[-1].split(".")[0]) if what in ("tabard", "trophy R", "trophy L") else 0
            if what.startswith("sheath"): kk = 0
            check(a, legs, o, what, src or s_, kk)
    models[m] = mine
m2 = models["m2"]
ck("m2: the right sheath brought the right plate (mirror variant)", any(cat(o) == "Hip Plates" and o.get("ws_snap_type") == "Plate R" and o.get("tiow_variant") is not None for o in m2), [(o.name, o.get("ws_snap_type")) for o in m2])
ck("m2: the tabard brought the buckle", any(cat(o) == "Buckles" and o.get("ws_snap_type") == "Buckle" for o in m2))
for m in models:
    for o in models[m]:
        if cat(o) in ("Plate Accessories", "Tabards"):
            host = T._snap_of(o)[0].parent
            ck("%s %s hangs from the %s" % (m, o.name, cat(host)), cat(host) == ("Hip Plates" if cat(o) == "Plate Accessories" else "Buckles"), cat(host))
scene = bpy.context.scene; rend.setup(scene, 600)
COL = {"Hip Plates": rend.BLUE, "Plate Accessories": (0.85, 0.3, 0.3, 1), "Buckles": (0.6, 0.45, 0.85, 1), "Tabards": (0.3, 0.75, 0.35, 1), "Trophies": (0.95, 0.6, 0.2, 1)}
for m in models:
    ob = [o for o in models[m] if cat(o) != "Chests"]
    rend.render(scene, "/home/claude/work/tlib_out", "tiow_" + m, ob, {"front": (0, 1, 0.2), "left": (-1, 0.1, 0.15), "right": (1, 0.1, 0.15)}, [COL.get(cat(o), rend.GREY) for o in ob], pad=1.05)
print("fails:", len(fails))
