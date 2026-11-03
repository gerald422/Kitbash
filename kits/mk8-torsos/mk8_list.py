import bpy, mathutils
bpy.ops.wm.open_mainfile(filepath="/home/claude/work/mk8/mk8.blend")
for c in bpy.data.collections:
    if not c.objects: continue
    print("==", c.name, "hide_render" if c.hide_render else "")
    for o in sorted(c.objects, key=lambda o:o.name):
        bb=[o.matrix_world@mathutils.Vector(v) for v in o.bound_box]
        mn=[min(v[i] for v in bb) for i in range(3)]; mx=[max(v[i] for v in bb) for i in range(3)]
        mods=",".join(f"{m.type}{'('+str(m.total_levels)+')' if m.type=='MULTIRES' else ''}" for m in o.modifiers)
        print(f"  {o.name:22s} {'H' if o.hide_get() or o.hide_viewport else ' '} v{len(o.data.vertices):7d} x[{mn[0]:6.1f},{mx[0]:6.1f}] y[{mn[1]:7.1f},{mx[1]:7.1f}] z[{mn[2]:5.1f},{mx[2]:5.1f}] rot{tuple(round(a,2) for a in o.rotation_euler)} sc{tuple(round(a,3) for a in o.scale)} {mods}")
print("orphan meshes:", [m.name for m in bpy.data.meshes if m.users==0][:20], "images:", len(bpy.data.images))
print("unit scale", bpy.context.scene.unit_settings.scale_length)
