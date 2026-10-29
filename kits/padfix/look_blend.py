import bpy, sys
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/issues with pauldrons.blend")
obs = bpy.data.objects
print(len(obs), "objects")
roots = [o for o in obs if o.parent is None and o.type == 'MESH']
for r in roots:
    print("ROOT", r.name, tuple(round(x, 1) for x in r.matrix_world.translation), r.get("tiow_model"), r.get("tiow_model_root"))
def walk(o, d=1):
    for c in o.children:
        if c.type == 'MESH':
            print("  " * d + c.name, "| src", str(c.get("tiow_src", ""))[-60:], "| hide", c.hide_get() if c.name in bpy.context.view_layer.objects else "?")
        walk(c, d + 1)
for r in roots: walk(r)
