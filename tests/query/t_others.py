"""Other belt bits on Legs 4B's corrected Hip R / Hip L / Belt Back: before (1.17.2, old sockets) and after
(1.17.3, corrected sockets). How deep each sits in / how far off the model, and a render of each."""
import bpy, json, os, sys, tempfile
sys.path.insert(0, "/home/claude/test"); import rend
from mathutils.bvhtree import BVHTree
LIB, TIOW, TAG = sys.argv[sys.argv.index("--") + 1:][:3]
CAP = "/home/claude/twoarm/caplib"
TOR = LIB + "/Turtle Ninja - Heresy/Mk7-8 Builder/Mk7-8/Chests/TN Mk7-8 - Upper B1.stl"
LEGS = LIB + "/Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 4B.stl"
ACC = LIB + "/Turtle Ninja - Tacticus/Mk10 Assault Intercessor + Jumppack Addon/Accessories/TN Mk10 Assault - Jump Pack Accessories %d.stl"
BITS = [(CAP + "/MarFil Jump Captain - Hip Plate With Holster.stl", "Hip R"), (CAP + "/MarFil Jump Captain - Hip Plate With Pouch.stl", "Hip R"),
        (ACC % 1, "Belt Back"), (ACC % 9, "Hip L")]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath=TIOW, overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
T.process_inbox()
scene = bpy.context.scene; rend.setup(scene, 420)
n = 0
for i, (bit, s) in enumerate(BITS):
    mid = "m%d" % i
    for p, cat, sock in [(TOR, "Chests", None), (LEGS, "Legs", None), (bit, "Accessories", s)]:
        r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": os.path.basename(p)[:-4], "category": cat,
             "tags": [], "itemId": "", "sentAt": "", "model": mid}
        if sock: r["socket"] = sock
        if cat == "Chests": r["at"] = [i * 60.0, 0, 0]
        n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
    T._state["beat"] = {}; T.process_inbox()
    obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH' and o.get("tiow_model") == mid]
    pl = next(o for o in obs if o.get("tiow_category") == "Accessories")
    hosts = [o for o in obs if o is not pl]
    dg = bpy.context.evaluated_depsgraph_get()
    best = 1e9
    for h in hosts:
        t = BVHTree.FromObject(h, dg); Wi = h.matrix_world.inverted()
        for v in pl.data.vertices:
            q = Wi @ (pl.matrix_world @ v.co); loc, nrm, _, d = t.find_nearest(q)
            if loc is not None:
                best = min(best, d if (q - loc).dot(nrm) >= 0 else -d)
    print("%s %-44s on %-9s %s; closest %+.2f mm" % (TAG, pl.name[:44], s, pl.get("ws_snap_type"), best))
    side = {"Hip R": (1, 0.25, 0.1), "Hip L": (-1, 0.25, 0.1), "Belt Back": (-0.2, -1, 0.1)}[s]
    rend.render(scene, "/home/claude/twoarm/query/out", "%s_%d" % (TAG, i), hosts + [pl], {"v": side},
                [rend.GREY] * len(hosts) + [rend.ORANGE], pad=1.05)
