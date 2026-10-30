"""The Jump Captain's hip plates through TIOW Inbox on three kinds of legs: snapped to Hip R / Hip L, settled onto the belt."""
import bpy, json, os, sys, tempfile
import numpy as np
sys.path.insert(0, "/home/claude/test"); import rend
from mathutils import Vector
from mathutils.bvhtree import BVHTree
LIB = "/mnt/user-data/uploads/d/Kitbash Library"; CAP = "/home/claude/twoarm/caplib"
TOR = LIB + "/Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 3.stl"
LEGS = [LIB + "/Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 1A.stl",
        LIB + "/Marta PunkGirl - Tacticus/51 May 2026/legs-chin pads and base/Legs/Marta May 2026 - Legs 1.stl",
        LIB + "/Turtle Ninja - Heresy/Mk2-6 Builder/Mk6/Legs/TN Mk6 - Lower A1.stl"]
SETS = [("MarFil Jump Captain - Hip Plate With Holster", "Hip R"), ("MarFil Jump Captain - Hip Plate With Scroll", "Hip L")]
SETS2 = [("MarFil Jump Captain - Hip Plate With Pouch", "Hip R"), ("MarFil Jump Captain - Relic", "Hip L")]
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d))); c or fails.append(l)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/tiow_117x/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
prefs.adaptor_dir = os.path.join(LIB, "Bits", "Adapters")
T.process_inbox()
scene = bpy.context.scene; rend.setup(scene, 520)
n = 0
for mi, legs in enumerate(LEGS):
    for si, sset in enumerate((SETS, SETS2)):
        mid = "m%d%d" % (mi, si)
        reqs = [(TOR, "Chests", None), (legs, "Legs", None)] + [(CAP + "/" + nm + ".stl", "Accessories", s) for nm, s in sset]
        for i, (p, cat, sock) in enumerate(reqs):
            r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": os.path.basename(p)[:-4], "category": cat, "tags": [], "itemId": "", "sentAt": "", "model": mid}
            if sock: r["socket"] = sock
            if cat == "Chests": r["at"] = [mi * 60.0, si * 60.0, 0]
            n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
        T._state["beat"] = {}; T.process_inbox()
        obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH' and o.get("tiow_model") == mid]
        lg = next((o for o in obs if o.get("tiow_category") == "Legs"), None)
        for nm, s in sset:
            pl = next((o for o in obs if o.name.startswith(nm[:40])), None)
            if pl is None or lg is None: ck("%s on %s: imported" % (nm.split(' - ')[1], os.path.basename(legs)[:-4]), False); continue
            sock = T._part_sockets()[1].snap_socket_of(pl)
            st = sock.get("ws_type") if sock is not None else None
            # gap / overlap with the legs: nearest distance from the plate to the legs, and how deep it goes in
            dg = bpy.context.evaluated_depsgraph_get()
            tl = BVHTree.FromObject(lg, dg); W = lg.matrix_world.inverted() @ pl.matrix_world
            d = [tl.find_nearest(W @ v.co)[3] for v in [pl.data.vertices[i] for i in range(0, len(pl.data.vertices), 7)]]
            ck("%-28s on %-26s snapped to %s, nearest %.2f mm" % (nm.split(' - ')[1], os.path.basename(legs)[:-4], st, min(d)), st == s and min(d) < 0.6, (st, min(d)))
        # render this model
        tor_o = next(o for o in obs if o.get("tiow_category") == "Chests")
        parts = [o for o in obs if o.get("tiow_category") in ("Chests", "Legs", "Adapters", "Accessories")]
        cols = [rend.GREY if o.get("tiow_category") != "Accessories" else rend.ORANGE for o in parts]
        rend.render(scene, "/home/claude/twoarm/bl/out", "belt_%s" % mid, parts, {"front": (0.35, 1, 0.15), "right": (1, -0.2, 0.1), "left": (-1, -0.2, 0.1), "back": (-0.3, -1, 0.15)}, cols, pad=1.05)
print("fails:", len(fails))
