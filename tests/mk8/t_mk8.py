"""Old Style Space Knight MK8 torsos, chest equipment, neck guards and bonus shin pads through TIOW Inbox 1.17.7.
m0: Mar Fil Torso 1 with Mar Fil legs, arms, head, pack and Mar Fil shin pads 6 (R) / 3 (L) (the baseline).
m1: MK8 Torso A0, same Mar Fil parts, Chest Equipment 1 L + R, Neck Guard 2, Shin Pad A (R) and B (L).
m2: MK8 Torso D0, Chest Equipment 4 R only, Neck Guard Collar, Shin Pad C (R). m3: Torso G9, Neck Guard 2.
Checks: chest equipment / neck guards land exactly as in the builder (R = mirror image); Mar Fil parts sit on the MK8
torso exactly as on Torso 1 (same sockets); a bonus shin pad lies on the shell of the Mar Fil pad it was lined up on.
python t_mk8.py -- WORKLIB TIOW_FILE OUTDIR"""
import bpy, json, os, sys, tempfile, struct
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/claude/test"); import rend
W, TIOW, OUT = sys.argv[sys.argv.index("--") + 1:][:3]
inv = np.linalg.inv
MF = W + "/Mar Fil - Tacticus/AssaultMarines-V2/"; K = W + "/Old Style Space Knight - Heresy/MK8/"
TOR1, LEGS = MF + "Chests/MarFil Assault - Torso 1.stl", MF + "Legs/MarFil Assault - Legs 1.stl"
ARMR, ARML = MF + "Arms/MarFil Assault - Arm 1B R.stl", MF + "Arms/MarFil Assault - Arm 1B L.stl"
HEAD, PACK = MF + "Helmet-Heads/Heads/MarFil Assault - Head 1.stl", MF + "Jump Packs/MarFil Assault - Jump Pack 1.stl"
MFSHIN = MF + "Knee Pads/MarFil Assault - Shin Pad %d.stl"
TOR = K + "Chests/OldStyle MK8 - Torso %s.stl"; CHEST = K + "Chest Equipment/OldStyle MK8 - Chest Equipment %d L.stl"
NECK = K + "Neck Guards/OldStyle MK8 - Neck Guard %s.stl"; SHIN = K + "Knee Pads/OldStyle MK8 - Shin Pad %s.stl"
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
T.process_inbox(); n = 0
def send(model, reqs, at):
    global n
    for p, cat, sock in reqs:
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": "", "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": model}
        if sock: r["socket"] = sock
        if cat == "Chests": r["at"] = at
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
BODY = [(LEGS, "Legs", "Waist"), (ARMR, "Arms", "Shoulder R"), (ARML, "Arms", "Shoulder L"), (HEAD, "Heads", "Neck"), (PACK, "Jump Packs", "Back")]
send("m0", [(TOR1, "Chests", None)] + BODY + [(MFSHIN % 6, "Knee Pads", "Shin R"), (MFSHIN % 3, "Knee Pads", "Shin L")], [0, 0, 0])
send("m1", [(TOR % "A0", "Chests", None)] + BODY + [(CHEST % 1, "Chest Equipment", "Chest Equip L"), (CHEST % 1, "Chest Equipment", "Chest Equip R"),
            (NECK % "2", "Neck Guards", "Neck Guard"), (SHIN % "A", "Knee Pads", "Shin R"), (SHIN % "B", "Knee Pads", "Shin L")], [80, 0, 0])
send("m2", [(TOR % "D0", "Chests", None), (LEGS, "Legs", "Waist"), (CHEST % 4, "Chest Equipment", "Chest Equip R"),
            (NECK % "Collar", "Neck Guards", "Neck Guard"), (SHIN % "C", "Knee Pads", "Shin R")], [160, 0, 0])
send("m3", [(TOR % "G9", "Chests", None), (LEGS, "Legs", "Waist"), (HEAD, "Heads", "Neck"), (NECK % "2", "Neck Guards", "Neck Guard")], [240, 0, 0])
obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH']
cat = lambda o: o.get("tiow_category")
def verts(o):
    v = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", v); return v.reshape(-1, 3)
def in_frame(o, host):     # o's vertices in host's file coordinates (mm)
    M = inv(np.array(host.matrix_world)) @ np.array(o.matrix_world); return (verts(o) @ M[:3, :3].T + M[:3, 3]) / float(host.get("tiow_unit", 1.0))
models = {}
for m in ("m0", "m1", "m2", "m3"):
    root = [o for o in obs if o.get("tiow_model") == m and o.get("tiow_model_root")][0]
    mine = [o for o in obs if T._model_root(o) is root]; models[m] = mine
    print(m, sorted((cat(o), o.get("ws_snap_type"), o.get("tiow_variant") is not None) for o in mine if o is not root))
    for o in mine:
        if cat(o) in ("Chest Equipment", "Neck Guards"):
            st = o.get("ws_snap_type"); P = in_frame(o, root); src = str(o.get("tiow_src") or "")
            nm = o.name.replace(" R", " L") if st == "Chest Equip R" else o.name
            f = [p for p in (CHEST % 1, CHEST % 4, NECK % "2", NECK % "Collar") if nm.startswith(os.path.basename(p)[:-4])]
            Q = stl(f[0]) if f else None
            if st == "Chest Equip R": Q = Q * [-1, 1, 1]
            d = cKDTree(Q).query(P)[0] if Q is not None else np.array([9e9])
            ck("%s %-34s on %-13s exactly as in the builder (max %.4f mm)%s" % (m, o.name[:34], st, d.max(), " [mirror variant]" if o.get("tiow_variant") is not None else ""),
               d.max() < 0.01 and (st != "Chest Equip R" or o.get("tiow_variant") is not None), (f, d.max()))
# Mar Fil parts sit on the MK8 torso as on Torso 1
r0 = [o for o in models["m0"] if o.get("tiow_model_root")][0]; r1 = [o for o in models["m1"] if o.get("tiow_model_root")][0]
for c, st in (("Legs", "Waist"), ("Arms", "Shoulder R"), ("Arms", "Shoulder L"), ("Heads", "Neck"), ("Jump Packs", "Back")):
    a = [o for o in models["m0"] if cat(o) == c and o.get("ws_snap_type") == st]; b = [o for o in models["m1"] if cat(o) == c and o.get("ws_snap_type") == st]
    ok = len(a) == 1 and len(b) == 1
    d = np.abs(in_frame(a[0], r0) - in_frame(b[0], r1)).max() if ok else 9e9
    ck("m1 Mar Fil %-10s on %-10s same place as on Torso 1 (%.4f mm)" % (c, st, d), ok and d < 0.01, d)
# bonus shin pads on the Mar Fil pad's shell (same legs)
leg = lambda m: [o for o in models[m] if cat(o) == "Legs"][0]
for m, st, mfm, mfn, lim in (("m1", "Shin R", "m0", 6, 0.06), ("m1", "Shin L", "m0", 3, 0.16), ("m2", "Shin R", "m0", 6, None)):
    a = [o for o in models[m] if cat(o) == "Knee Pads" and o.get("ws_snap_type") == st]
    b = [o for o in models[mfm] if cat(o) == "Knee Pads" and o.get("ws_snap_type") == st]
    if not (a and b): ck("%s %s shin pad placed" % (m, st), False); continue
    if lim is None:
        ck("%s %s shin pad placed (%s)" % (m, st, a[0].name), True); continue
    d = cKDTree(in_frame(b[0], leg(mfm))).query(in_frame(a[0], leg(m)))[0]
    ck("%s %-6s %-26s on Mar Fil pad %d's shell: median %.3f mm" % (m, st, a[0].name[:26], mfn, np.median(d)), np.median(d) < lim, np.median(d))
scene = bpy.context.scene; rend.setup(scene, 560)
COL = {"Chest Equipment": rend.ORANGE, "Neck Guards": rend.BLUE, "Knee Pads": rend.GREEN, "Chests": (0.7, 0.7, 0.66, 1)}
for m in models:
    rend.render(scene, OUT, "mk8_" + m, models[m], {"front": (0.35, 1, 0.25), "back": (-0.5, -1, 0.5)}, [COL.get(cat(o), rend.GREY) for o in models[m]], pad=1.05)
print("fails:", len(fails))
