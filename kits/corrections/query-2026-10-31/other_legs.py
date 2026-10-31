import bpy, sys, os, json, tempfile, shutil
from mathutils.bvhtree import BVHTree
sys.path.insert(0, "/home/claude/test"); import rend
W = "/home/claude/twoarm/loin/work"; R = "Marta PunkGirl - Tacticus/51 May 2026/loincloths/Accessories/Marta May 2026 - Loincloth 3"
TOR = W + "/Turtle Ninja - Heresy/Mk7-8 Builder/Mk7-8/Chests/TN Mk7-8 - Upper B1.stl"
LEGS = [W + "/Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 4B.stl",
        W + "/Marta PunkGirl - Tacticus/51 May 2026/legs-chin pads and base/Legs/Marta May 2026 - Legs 1.stl"]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/kitbash/addons/tiow_inbox.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="tiow_inbox")
import tiow_inbox as T
prefs = T.get_prefs(); prefs.inbox_path = tempfile.mkdtemp()
inbox = os.path.join(tempfile.mkdtemp(), "_builder", "inbox"); os.makedirs(inbox); prefs.builder_inbox = inbox
prefs.adaptor_dir = os.path.join(W, "Bits", "Adapters"); T.process_inbox()
scene = bpy.context.scene; rend.setup(scene, 420)
n = 0
for tag, side in (("before", "/home/claude/twoarm/query2/old_loin3.json"), ("after", "/home/claude/twoarm/query2/new_loin3.json")):
    shutil.copy(side, W + "/" + R + ".sockets.json"); T._lib_cache.clear() if hasattr(T, "_lib_cache") else None
    for i, legs in enumerate(LEGS):
        mid = "%s%d" % (tag, i)
        for p, c, s in [(TOR, "Chests", None), (legs, "Legs", None), (W + "/" + R + ".stl", "Loincloths", "Belt Front")]:
            r = {"schemaVersion": 1, "path": p, "name": os.path.basename(p)[:-4], "title": "", "category": c, "tags": [], "itemId": "", "sentAt": "", "model": mid}
            if s: r["socket"] = s
            if c == "Chests": r["at"] = [n * 30.0, 0, 0]
            n += 1; json.dump(r, open(os.path.join(inbox, "sb-%04d.json" % n), "w"))
        T._state["beat"] = {}; T.process_inbox()
        obs = [o for o in bpy.context.view_layer.objects if o.type == 'MESH' and o.get("tiow_model") == mid]
        pl = next(o for o in obs if o.get("tiow_category") == "Loincloths"); lg = next(o for o in obs if o.get("tiow_category") == "Legs")
        S = T._snap_of(pl)[0].matrix_world.inverted()
        dg = bpy.context.evaluated_depsgraph_get(); t = BVHTree.FromObject(lg, dg); Wi = lg.matrix_world.inverted()
        top = 9
        for v in [pl.data.vertices[k] for k in range(0, len(pl.data.vertices), 3)]:
            w = pl.matrix_world @ v.co
            if (S @ w).y < -6: continue
            q = Wi @ w; loc, nrm, _, d = t.find_nearest(q)
            if loc is not None: top = min(top, d if (q - loc).dot(nrm) >= 0 else -d)
        print("%-6s on %-26s top 6 mm: deepest %+.2f mm" % (tag, os.path.basename(legs)[:-4], top))
        others = [o for o in obs if o is not pl]
        rend.render(scene, "/home/claude/twoarm/query2/out", mid, others + [pl], {"side": (1, 0.2, 0.05), "front": (0.15, 1, 0.05)},
                    [rend.GREY] * len(others) + [rend.ORANGE], pad=1.03)
        for o in obs: o.hide_render = True
