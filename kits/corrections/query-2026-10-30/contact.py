import bpy, sys
from mathutils.bvhtree import BVHTree
f = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=f)
dg = bpy.context.evaluated_depsgraph_get()
legs = next(o for o in bpy.data.objects if o.get("tiow_category") == "Legs")
others = [o for o in bpy.data.objects if o.type == 'MESH' and o.get("tiow_category") in ("Legs", "Jump Packs", "Chests")]
trees = [(o, BVHTree.FromObject(o, dg)) for o in others]
for o in bpy.data.objects:
    if o.get("tiow_category") != "Accessories": continue
    unit = float(o.get("tiow_unit", 1.0))
    best = 1e9; deep = 0.0
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        for h, t in trees:
            loc, nrm, i, d = t.find_nearest(h.matrix_world.inverted() @ w)
            if loc is None: continue
            sd = (h.matrix_world.inverted() @ w - loc).dot(nrm)
            sd = (d if sd >= 0 else -d) / unit
            best = min(best, sd)
    print("%-44s %-11s closest %+.2f mm (negative = inside)" % (o.name[:44], o.get("ws_snap_type"), best))
