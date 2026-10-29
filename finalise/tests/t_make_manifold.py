"""Finalise 0.3.3: 'Make them manifold first (3D Print Toolbox)' fixes Finalise's copy of an
open part so it booleans with Manifold; your original is untouched; without the toolbox the box is off."""
import bpy, bmesh, sys, os, shutil, addon_utils
from mathutils import Matrix
bpy.ops.wm.read_factory_settings(use_empty=True)
# the 3D Print Toolbox from Josh's Blender, as an add-on here
dst = os.path.join(bpy.utils.user_resource('SCRIPTS', path="addons"), "print3d_toolbox")
shutil.rmtree(dst, ignore_errors=True)
shutil.copytree("/mnt/user-data/uploads/5.1/extensions/blender_org/print3d_toolbox", dst)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise_034/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d)))
    if not c: fails.append(l)
ck("no toolbox yet: the option is unavailable", not KF.toolbox_ready())
try:
    bpy.ops.preferences.addon_enable(module="print3d_toolbox")
except Exception as exc:
    print("enable failed:", exc)
ck("toolbox enabled: Make Manifold available", KF.toolbox_ready())
ctx = bpy.context; scene = ctx.scene; vl = ctx.view_layer
def mesh_obj(name, fn):
    bm = bmesh.new(); fn(bm); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return ob
def sock(name, parent, mat, t):
    e = bpy.data.objects.new(name, None); scene.collection.objects.link(e); e['ws_type'] = t
    e.parent = parent; e.matrix_world = mat; return e
def open_box(bm):
    bmesh.ops.create_cube(bm, size=4.0, matrix=Matrix.Translation((7, 0, 0)))
    bm.faces.ensure_lookup_table()
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    bmesh.ops.delete(bm, geom=[top], context='FACES_ONLY')
body = mesh_obj("Body", lambda bm: bmesh.ops.create_cube(bm, size=10.0))
s1 = sock("Body_socket_Shoulder R", body, Matrix.Translation((5, 0, 0)), "Shoulder R")
box = mesh_obj("Box", open_box)
box.parent = s1; box.matrix_parent_inverse = s1.matrix_world.inverted()
before = len(box.data.polygons)
for o in vl.objects: o.select_set(False)
body.select_set(True); vl.objects.active = body
root, parts = KF.FA_OT_finalise._scan(None, ctx)
wm = ctx.window_manager
ck("the open box is listed as not manifold", [b.part for b in wm.fa_bad] == ['Box'], [(b.part, b.info) for b in wm.fa_bad])
r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=False, use_exact=False, make_manifold=True)
print(scene.fa_last_log)
ck("finalise ran with only 'make manifold' ticked", r == {'FINISHED'}, r)
ck("log says it was made manifold", "Box: made manifold" in scene.fa_last_log, scene.fa_last_log)
h = [o for o in bpy.data.objects if o.get('fa_role') == 'host'][0]
mods = [(m.operation, m.solver, m.object.name) for m in h.modifiers]
ck("its union uses the Manifold solver", all(m[1] == 'MANIFOLD' for m in mods) and any(m[2].startswith('Box') for m in mods), mods)
copy = next(o for o in bpy.data.objects if o.get('fa_src') == 'Box')
ck("Finalise's copy is closed", KF.manifold_report(copy, ctx.evaluated_depsgraph_get()) == "")
ck("your original is untouched", len(box.data.polygons) == before and KF.manifold_report(box, ctx.evaluated_depsgraph_get()) != "")
ck("back in Object Mode", ctx.mode == 'OBJECT', ctx.mode)
r = bpy.ops.fa.apply('EXEC_DEFAULT'); print(scene.fa_last_log)
ck("baked piece manifold", "manifold" in scene.fa_last_log and "open" not in scene.fa_last_log, scene.fa_last_log)
print("FAILS:", fails)
