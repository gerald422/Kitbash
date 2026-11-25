"""batch.py build --then: a flat floor under each column's legs, at its legs' lowest point (notes 142): legs that
lean touch it with one foot only. (One shared height doesn't work: Redwarden stands 17 mm lower.)
Runs with objs (kb_id -> object), spec, bpy, np, G."""
import bpy, numpy as np


def low(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    W = np.array(o.matrix_world); v = np.array([x.co[:] for x in m.vertices]); e.to_mesh_clear()
    v = v @ W[:3, :3].T + W[:3, 3]; return v


bpy.context.view_layer.update()
coll = bpy.data.collections.new("Floor (flat, under each column's legs)"); bpy.context.scene.collection.children.link(coll)
mat = bpy.data.materials.new("kb floor"); mat.diffuse_color = (0.35, 0.55, 0.85, 0.35)
for e in spec["objects"]:
    if e["role"] != "host": continue
    v = low(objs[e["id"] + "_legs"]); cx, cy = (v[:, 0].min() + v[:, 0].max()) / 2, (v[:, 1].min() + v[:, 1].max()) / 2; z = v[:, 2].min()
    me = bpy.data.meshes.new("floor"); r = 30.0
    t = 0.4                                          # a thin slab, so it shows as a line from the front or side
    V = [(cx + a * r, cy + b * r, z - c * t) for c in (0, 1) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    me.from_pydata(V, [], [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    me.materials.append(mat)
    o = bpy.data.objects.new("Floor " + e.get("name", e["id"])[:40], me); coll.objects.link(o)
    o.hide_select = True; o.display_type = 'SOLID'; o.show_transparent = True
    print("floor under %-6s z %.2f" % (e["id"], z))
