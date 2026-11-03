"""Library holsters, pouches and grenades on the hip plate (Nov 3, plates only) through TIOW Inbox 1.17.7 on Mar Fil
Assault Legs 4A, sent like the Squad Builder does (model + socket). Each part must land where the fit rule put it
(hol_fit.py: Plate Hang socket · fit; the right side the mirror image), on the plate of its side; a holster sent
before the plate brings it; the Outrider right file goes on the right as itself (no mirror).
python t_holsters.py -- WORKLIB TIOW_FILE FITS_JSON OUTDIR"""
import bpy, json, os, sys, tempfile, struct
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/claude/test"); import rend
W, TIOW, FJ, OUT = sys.argv[sys.argv.index("--") + 1:][:4]
M16 = lambda a: np.array(a, float).reshape(4, 4); inv = np.linalg.inv; A = np.diag([-1.0, 1, 1, 1])
AM = W + "/Mar Fil - Tacticus/AssaultMarines-V2/"
TOR, LEGS, PLATE = AM + "Chests/MarFil Assault - Torso 1.stl", AM + "Legs(JumpPack)/Legs/MarFil Assault - Legs 4A.stl", AM + "Hip Plates/MarFil Assault - Hip Plate L.stl"
P = {"tn": "Turtle Ninja - Heresy/Mk6 Addon 1/Accessories/TN Mk6 Addon - Holster Pistol", "orL": "Mar Fil - Tacticus/Outriders/Accessories/MarFil Outrider - Holster 1 L",
     "orR": "Mar Fil - Tacticus/Outriders/Accessories/MarFil Outrider - Holster 1", "bb": "BBoosty - Heresy/Medusas Mortals/Stuff/Accessories/BBoosty Medusas Mortals - Holster Skull Bolt Pistol",
     "gr": "Turtle Ninja - Heresy/Mk4 Tactical Squad/Accessories/Grenades/TN Mk4 Tactical - Accessory Grenade 1", "tm": "Mar Fil - Tacticus/Techmarine/Accessories/MarFil Techmarine - Pistol Holster 2",
     "mb": "BBoosty - Heresy/Medusas Mortals/Stuff/Grenades/BBoosty Medusas Mortals - Melta Bomb"}
FITS = {k.replace("\\", "/")[:-4]: M16(v["fit"]) for k, v in json.load(open(FJ)).items()}
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
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox(); n = 0
def send(model, reqs, at):
    global n
    for p, cat, sock in reqs:
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": model}
        if sock: r["socket"] = sock
        if cat == "Chests": r["at"] = at
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
S = lambda k: W + "/" + P[k] + ".stl"; PA = "Plate Accessories"
send("m1", [(TOR, "Chests", None), (LEGS, "Legs", "Waist"), (PLATE, "Hip Plates", "Plate L"), (PLATE, "Hip Plates", "Plate R"),
            (S("tn"), PA, "Plate Hang L"), (S("tn"), PA, "Plate Hang R")], [0, 0, 0])
send("m2", [(TOR, "Chests", None), (LEGS, "Legs", "Waist"), (S("orL"), PA, "Plate Hang L"), (S("orR"), PA, "Plate Hang R")], [80, 0, 0])
send("m3", [(TOR, "Chests", None), (LEGS, "Legs", "Waist"), (S("bb"), PA, "Plate Hang R"), (S("gr"), PA, "Plate Hang L")], [160, 0, 0])
send("m4", [(TOR, "Chests", None), (LEGS, "Legs", "Waist"), (S("tm"), PA, "Plate Hang R"), (S("mb"), PA, "Plate Hang L")], [240, 0, 0])
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
cat = lambda o: o.get("tiow_category")
def verts(o):
    v = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", v); return v.reshape(-1, 3)
def in_frame(o, host):
    M = inv(np.array(host.matrix_world)) @ np.array(o.matrix_world); return (verts(o) @ M[:3, :3].T + M[:3, 3]) / float(host.get("tiow_unit", 1.0))
models = {}
for m, items in (("m1", [("tn", "L"), ("tn", "R")]), ("m2", [("orL", "L"), ("orR", "R")]), ("m3", [("bb", "R"), ("gr", "L")]), ("m4", [("tm", "R"), ("mb", "L")])):
    root = [o for o in obs if o.get("tiow_model") == m and o.get("tiow_model_root")][0]
    mine = [o for o in obs if T._model_root(o) is root]; models[m] = mine
    plates = {o.get("ws_snap_type")[-1]: o for o in mine if cat(o) == "Hip Plates"}
    for k, sd in items:
        o = [x for x in mine if cat(x) == PA and x.get("ws_snap_type") == "Plate Hang " + sd and os.path.basename(P[k]).split(" - ")[1].split(" ")[0] in x.name]
        if not o or sd not in plates: ck(f"{m} {k} on Plate Hang {sd} (plate there)", False, [(x.name, x.get('ws_snap_type')) for x in mine]); continue
        o = o[0]; pl = plates[sd]; host = o.parent if o.parent is not None else pl
        Pts = in_frame(o, pl)                                       # the part in its plate's file frame
        ph = json.load(open(AM + "Hip Plates/MarFil Assault - Hip Plate L.sockets.json"))
        SPH = M16([s for s in ph["sockets"] if s["type"] == "Plate Hang L"][0]["matrix"])
        V = stl(S(k))
        if k == "orR":
            E = A @ SPH @ A @ A @ FITS[P["orL"]] @ np.diag([1.0, -1, 1, 1]); Q = V @ E[:3, :3].T + E[:3, 3]   # right plate = mirror frame
        elif sd == "L":
            E = SPH @ FITS[P[k]]; Q = V @ E[:3, :3].T + E[:3, 3]
        else:
            E = A @ SPH @ FITS[P[k]]; Q = V @ E[:3, :3].T + E[:3, 3]                                          # mirror of the left placement
        if sd == "R" and pl.get("tiow_variant") is not None: Q = Q                                            # the right plate is itself the mirror variant
        d = cKDTree(Q).query(Pts[::3])[0]
        ck(f"{m} {o.name[:44]:44s} on Plate Hang {sd}: {d.max():.4f} mm from the rule{' [mirror variant]' if o.get('tiow_variant') is not None else ''}", d.max() < 0.01, d.max())
    if m == "m3": ck("m3 a holster sent first brought its plate", "R" in plates and "L" in plates, list(plates))
    if m == "m2": ck("m2 the Outrider right file is itself, not a mirror", all(x.get("tiow_variant") is None for x in mine if cat(x) == PA), [(x.name, x.get("tiow_variant")) for x in mine if cat(x) == PA])
scene = bpy.context.scene; rend.setup(scene, 520)
COL = {"Hip Plates": rend.BLUE, PA: rend.ORANGE}
for m in models:
    ob = [o for o in models[m] if cat(o) != "Chests"]
    rend.render(scene, OUT, "hol_" + m, ob, {"left": (-1, 0.25, 0.15), "right": (1, 0.25, 0.15)}, [COL.get(cat(o), rend.GREY) for o in ob], pad=1.05)
print("fails:", len(fails))
