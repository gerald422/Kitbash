"""Loincloths through TIOW Inbox 1.17.4: their own type, on Belt Front only, rocked and settled onto the belt; a belt
bit with a Belt Front fit sent without a socket now goes on a hip or the back of the belt, never the front.
Usage: python t_loin.py WORKLIB TIOW_FILE"""
import bpy, json, os, sys, tempfile
sys.path.insert(0, "/home/claude/test"); import rend
from mathutils.bvhtree import BVHTree
W, TIOW = sys.argv[1], sys.argv[2]
TOR = W + "/Turtle Ninja - Heresy/Mk7-8 Builder/Mk7-8/Chests/TN Mk7-8 - Upper B1.stl"
L4B = W + "/Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 4B.stl"
MAR = W + "/Marta PunkGirl - Tacticus/51 May 2026/legs-chin pads and base/Legs/Marta May 2026 - Legs 1.stl"
CB = W + "/CyberBrush - Tacticus/Space Bugs Hunters/Space Bug Hunters Loinclothes/Accessories/CyberBrush Bug Hunters - Loinclothe %d.stl"
ML1 = W + "/Marta PunkGirl - Tacticus/51 May 2026/loincloths/Accessories/Marta May 2026 - Loincloth 1.stl"
MJ3 = W + "/Marta PunkGirl - Tacticus/53 July 2026/loincloths/Accessories/Marta Jul 2026 - Loincloth 3.stl"
ACC2 = W + "/Turtle Ninja - Tacticus/Mk10 Assault Intercessor + Jumppack Addon/Accessories/TN Mk10 Assault - Jump Pack Accessories 2.stl"
MODELS = [(L4B, CB % 1, "Belt Front"), (L4B, CB % 4, "Belt Front"), (MAR, CB % 2, "Belt Front"), (MAR, ML1, "Belt Front"),
          (L4B, MJ3, "Belt Front"), (L4B, ACC2, None)]
TOP = {MJ3: -1.6}     # Marta's Jul 3 (her own fit, unchanged): its top sits 1.4 mm into a Mar Fil belt, as it did as an Accessory
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
ck("TIOW Inbox 1.17.4", T.bl_info["version"] == (1, 17, 4), T.bl_info["version"])
ck("Loincloths: Belt Front only; belt bits not on it", T.DEFAULT_JOINTS["Loincloths"]["socket"] == "Belt Front"
   and all("Belt Front" not in T.DEFAULT_JOINTS[c]["socket"] for c in ("Accessories", "Grenades", "Seals", "Trophies")))
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
prefs.adaptor_dir = os.path.join(W, "Bits", "Adapters")
T.process_inbox()
scene = bpy.context.scene; rend.setup(scene, 360)
n = 0
for i, (legs, bit, sock) in enumerate(MODELS):
    mid = "m%d" % i
    cat = json.load(open(bit[:-4] + ".sockets.json", encoding="utf-8"))["category"]
    for p, c, s in [(TOR, "Chests", None), (legs, "Legs", None), (bit, cat, sock)]:
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": os.path.basename(p)[:-4], "category": c,
             "tags": [], "itemId": "", "sentAt": "", "model": mid}
        if s: r["socket"] = s
        if c == "Chests": r["at"] = [i * 60.0, 0, 0]
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
    obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH' and o.get("tiow_model") == mid]
    pl = next(o for o in obs if o.get("tiow_category") == cat)
    lg = next(o for o in obs if o.get("tiow_category") == "Legs")
    st = pl.get("ws_snap_type")
    nm = "%s on %s" % (os.path.basename(bit)[:-4].split(" - ")[1], os.path.basename(legs)[:-4].split(" - ")[1])
    if sock is None:
        ck("%s (Accessories, no socket asked): went on %s, not the front" % (nm, st), st in ("Hip R", "Hip L", "Belt Back"), st)
        continue
    # the top (down to 8 mm below the anchor) sits on the belt; lower down a rigid cloth can meet a raised thigh
    dg = bpy.context.evaluated_depsgraph_get()
    t = BVHTree.FromObject(lg, dg); Wi = lg.matrix_world.inverted()
    S = T._part_sockets()[1].snap_socket_of(pl).matrix_world.inverted()
    top, low = 1e9, 1e9
    for k in range(0, len(pl.data.vertices), 5):
        w = pl.matrix_world @ pl.data.vertices[k].co; q = Wi @ w; loc, nrm, _, d = t.find_nearest(q)
        if loc is not None:
            sd = d if (q - loc).dot(nrm) >= 0 else -d
            if (S @ w).y > -8.0: top = min(top, sd)
            else: low = min(low, sd)
    ck("%-26s category %s, on %s; top on the belt %+.2f mm (lower down %+.1f)" % (nm, pl.get("tiow_category"), st, top, low),
       st == "Belt Front" and pl.get("tiow_category") == "Loincloths" and TOP.get(bit, -0.6) < top < 0.6, (st, top))
    tor = next(o for o in obs if o.get("tiow_category") == "Chests")
    rend.render(scene, "/home/claude/twoarm/loin/out", "loin_%d" % i, [o for o in obs if o is not pl] + [pl],
                {"front": (0.25, 1, 0.1), "side": (1, 0.15, 0.05)}, [rend.GREY] * (len(obs) - 1) + [rend.ORANGE], pad=1.05)
print("fails:", len(fails))
