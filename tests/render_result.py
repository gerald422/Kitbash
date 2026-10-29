import bpy, sys, json
from mathutils import Vector, Matrix
bpy.ops.wm.open_mainfile(filepath="/home/claude/test/pads_result.blend", load_ui=False)
sc = bpy.context.scene
groups = json.loads(sys.argv[-2]); outdir = sys.argv[-1]
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'OBJECT'
sc.display.shading.show_cavity = True; sc.render.resolution_x = 560; sc.render.resolution_y = 560
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.clip_end = 3000
PAL = [(0.78, 0.78, 0.74, 1), (0.45, 0.65, 0.85, 1), (0.85, 0.55, 0.35, 1), (0.6, 0.8, 0.5, 1)]
for g in groups:
    show = [bpy.data.objects[n] for n in g['objects']]
    for o in sc.objects:
        if o.type == 'MESH': o.hide_render = o not in show
    for i, o in enumerate(show): o.color = PAL[i % 4]
    pts = [o.matrix_world @ Vector(c) for o in show for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; size = (hi - lo).length
    for name, d in g['views'].items():
        d = Vector(d).normalized(); up = Vector((0, 0, 1)) if abs(d.z) < 0.99 else Vector((0, 1, 0))
        y = (up - d * up.dot(d)).normalized(); x = y.cross(d)
        cam.matrix_world = Matrix.LocRotScale(c + d * (size * 3 + 50), Matrix((x, y, d)).transposed().to_quaternion(), None)
        cam.data.ortho_scale = size * 1.05
        sc.render.filepath = f"{outdir}/{g['name']}_{name}.png"; bpy.ops.render.render(write_still=True)
