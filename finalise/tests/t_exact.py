"""Exact path on small meshes: a non-manifold part is listed, refused without Exact, booleaned last with Exact."""
import bpy, bmesh, sys
from mathutils import Matrix, Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
ctx = bpy.context; scene = ctx.scene; vl = ctx.view_layer
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d)))
    if not c: fails.append(l)
def mesh_obj(name, fn, **kw):
    bm = bmesh.new(); fn(bm, **kw); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return ob
def sock(name, parent, mat, t):
    e = bpy.data.objects.new(name, None); scene.collection.objects.link(e); e['ws_type'] = t
    e.parent = parent; e.matrix_world = mat; return e
body = mesh_obj("Body", lambda bm: bmesh.ops.create_cube(bm, size=10.0))
s1 = sock("Body_socket_Shoulder R", body, Matrix.Translation((5, 0, 0)), "Shoulder R")
arm = mesh_obj("Arm", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=2.5, radius2=2.5, depth=8,
                                                       matrix=Matrix.Translation((4, 0, 0)) @ Matrix.Rotation(1.5708, 4, 'Y')))
arm.parent = s1; arm.matrix_parent_inverse = s1.matrix_world.inverted()
s2 = sock("Arm_socket_Hand R", arm, Matrix.Translation((9, 0, 0)), "Hand R")
gun = mesh_obj("Gun", lambda bm: bmesh.ops.create_grid(bm, x_segments=4, y_segments=4, size=2.0, matrix=Matrix.Translation((9.5, 0, 0)) @ Matrix.Rotation(1.5708, 4, 'X')))
gun.parent = s2; gun.matrix_parent_inverse = s2.matrix_world.inverted()
pad = mesh_obj("Pad", lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=3, radius=2.0, matrix=Matrix.Translation((6, 0, 3))))
s3 = sock("Arm_socket_Pad R", arm, Matrix.Translation((6, 0, 3)), "Pad R")
pad.parent = s3; pad.matrix_parent_inverse = s3.matrix_world.inverted()
for o in vl.objects: o.select_set(False)
body.select_set(True); vl.objects.active = body
root, parts = KF.FA_OT_finalise._scan(None, ctx)
wm = ctx.window_manager
ck("non-manifold gun listed", [b.part for b in wm.fa_bad] == ['Gun'], [(b.part, b.info) for b in wm.fa_bad])
for it in wm.fa_items: it.split = it.part == 'Arm'
try:
    r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True, use_exact=False)
except RuntimeError: r = {'CANCELLED'}
ck("refused without Exact", r == {'CANCELLED'})
ck("nothing built when refused", not any(o.get('fa_build') for o in bpy.data.objects))
r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True, use_exact=True)
print(scene.fa_last_log)
h = [o for o in bpy.data.objects if o.get('fa_role') == 'host' and o.get('fa_src') == 'Arm'][0]
mods = [(m.operation, m.solver, m.object.name) for m in h.modifiers]
print(mods)
gi = next(i for i, m in enumerate(mods) if m[2].startswith('Gun'))
ck("gun unioned with Exact", mods[gi][1] == 'EXACT', mods)
ck("Manifold before it, Exact from it on (order kept)", all(m[1] == 'MANIFOLD' for m in mods[:gi]) and all(m[1] == 'EXACT' for m in mods[gi:]), mods)
ck("parts, then peg, then letter", [m[0] for m in mods][-2:] == ['UNION', 'DIFFERENCE'] and 'FA_peg' in mods[-2][2] and 'FA_letter' in mods[-1][2], mods)
bh = [o for o in bpy.data.objects if o.get('fa_role') == 'host' and o.get('fa_src') == 'Body'][0]
print([(m.operation, m.solver, m.object.name) for m in bh.modifiers])
ck("body has cavity or peg, carves (arm + pad overlap it), one letter", len(bh.modifiers) == 4, [m.object.name for m in bh.modifiers])
lets = [o for o in bpy.data.objects if o.get('fa_role') == 'letter']
ck("one letter per piece (body + arm)", len(lets) == 2, [o.name for o in lets])
ck("same letter on both", all(o.name.startswith('FA_letter_A_') for o in lets), [o.name for o in lets])
r = bpy.ops.fa.apply('EXEC_DEFAULT'); print(scene.fa_last_log)
ck("baked 2 pieces", len([o for o in bpy.data.objects if o.get('fa_role') == 'piece']) == 2)
ck("body manifold after", "Body [A]: manifold" in scene.fa_last_log, scene.fa_last_log)
ck("arm reported (its open gun went in with Exact)", "Arm [A]:" in scene.fa_last_log, scene.fa_last_log)
# discard restores the originals
vl.objects.active = [o for o in bpy.data.objects if o.get('fa_role') == 'piece'][0]
bpy.ops.fa.discard('EXEC_DEFAULT')
ck("discard: originals visible again", all(o.visible_get() for o in (body, arm, gun, pad)))
ck("discard: build gone", not any(o.get('fa_build') for o in bpy.data.objects) and not any(c.get('fa_build') for c in bpy.data.collections))
print("FAILS:", fails)
