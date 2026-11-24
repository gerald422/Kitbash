"""Check renders for the by-eye checks (skill `kitbash-seat-by-shape`, Checks), inside Blender, Workbench.
Moved from the Nov 23 scripts (render_cmp, render_belt, buckle_apply's shots). A camera is set from a frame F (world
4x4): the view direction d and up are given in F's own axes, so every candidate is seen the same way.
  close-up of a pad: views from the guide's axes: outside, front, back, under the rim
  legs: a front render of the belt only, about 13 mm wide (at 50 mm a 12 deg turn is invisible), plus a top slice"""
import os
import bpy
from mathutils import Matrix, Vector

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
PAD_VIEWS = [("outside", X + Z * 0.3), ("front", Y + Z * 0.3), ("back", -Y + Z * 0.3), ("under rim", -Z + X * 0.25)]


def setup(res=360, cavity=1.0):
    sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
    sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True
    if cavity != 1.0: sh.cavity_type = "BOTH"; sh.cavity_ridge_factor = cavity; sh.cavity_valley_factor = cavity
    if not sc.world: sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0.93, 0.93, 0.93); sc.render.resolution_x = sc.render.resolution_y = res
    cam = bpy.data.objects.get("kb check camera")
    if cam is None:
        cam = bpy.data.objects.new("kb check camera", bpy.data.cameras.new("kb check camera")); sc.collection.objects.link(cam)
    sc.camera = cam; cam.data.type = "ORTHO"; cam.data.clip_end = 1000; return cam


def shoot(cam, path, F, cen, d, upv, scale, clip=(0.1, 1000), dist=150):
    """render to path: looking along -d (d, upv in F's axes) at world point cen, ortho width scale mm"""
    R = F.to_3x3().normalized(); d = (R @ Vector(d)).normalized(); upv = R @ Vector(upv)
    cam.data.ortho_scale = scale; cam.data.clip_start, cam.data.clip_end = clip; loc = cen + d * dist
    up = upv - d * upv.dot(d)
    if up.length < 1e-3: up = R @ X - d * (R @ X).dot(d)
    up.normalize(); r = up.cross(d).normalized()
    cam.matrix_world = Matrix(((r.x, up.x, d.x, loc.x), (r.y, up.y, d.y, loc.y), (r.z, up.z, d.z, loc.z), (0, 0, 0, 1)))
    bpy.context.scene.render.filepath = path; bpy.ops.render.render(write_still=True)


def only(objs):
    """render only these objects"""
    keep = set(objs)
    for o in bpy.data.objects: o.hide_render = o not in keep and o.type != 'CAMERA'


def pad_views(cam, out_dir, guide, label, scale=22):
    """the four close-ups of a guide (and its pad) on its arm, from the guide's own axes"""
    F = guide.matrix_world; cen = F.translation - F.to_3x3().normalized().col[2] * 3; paths = []
    for v, (vn, d) in enumerate(PAD_VIEWS):
        p = os.path.join(out_dir, "%s_%d %s.png" % (label, v, vn)); shoot(cam, p, F, cen, d.normalized(), Z, scale); paths.append(p)
    return paths


def belt_views(cam, out_dir, torso, cx, cy, zt, label):
    """front of the belt (13 mm) and a top slice of the belt band, in the torso's frame (cx, cy, zt: waist centre top)"""
    F = torso.matrix_world; a = os.path.join(out_dir, label + "_front.png"); b = os.path.join(out_dir, label + "_top.png")
    shoot(cam, a, F, F @ Vector((cx, cy, zt - 1.8)), Y, Z, 13)
    shoot(cam, b, F, F @ Vector((cx, cy, zt)), Z, Y, 15, clip=(150.3, 152.6)); return [a, b]
