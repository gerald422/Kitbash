"""Workbench render helpers for the headless tests."""
import bpy, os
from mathutils import Matrix, Vector
GREY, BLUE, ORANGE, GREEN, PURPLE, RED = (0.8, 0.8, 0.76, 1), (0.45, 0.65, 0.88, 1), (0.9, 0.58, 0.35, 1), (0.55, 0.8, 0.5, 1), (0.75, 0.55, 0.85, 1), (0.9, 0.35, 0.35, 1)
def setup(scene, res=620):
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'OBJECT'; scene.display.shading.show_cavity = True
    scene.render.resolution_x = scene.render.resolution_y = res
    if scene.world is None: scene.world = bpy.data.worlds.new("w")
    cam = bpy.data.objects.get("cam")
    if cam is None:
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam)
    scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.clip_end = 5000
    return cam
def render(scene, out, name, obs, views, colors, frame=None, pad=1.02, up=(0, 0, 1)):
    """views: name -> direction from the target to the camera (world, or in `frame` axes)."""
    cam = scene.camera
    for o in scene.objects:
        if o.type == 'MESH': o.hide_render = o not in obs
        if o.type == 'EMPTY': o.hide_render = True
    for o, c in zip(obs, colors): o.color = c
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (lo + hi) / 2; size = (hi - lo).length
    R = frame.to_3x3().normalized() if frame is not None else Matrix.Identity(3)
    files = {}
    for vname, d in views.items():
        d = (R @ Vector(d)).normalized(); u = R @ Vector(up)
        if abs(u.normalized().dot(d)) > 0.99: u = R @ Vector((0, 1, 0))
        y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
        cam.matrix_world = Matrix.LocRotScale(c + d * (size * 3 + 50), Matrix((x, y, d)).transposed().to_quaternion(), None)
        cam.data.ortho_scale = size * pad
        f = f"{out}/{name}_{vname}.png"; scene.render.filepath = f; bpy.ops.render.render(write_still=True); files[vname] = f
    return files
