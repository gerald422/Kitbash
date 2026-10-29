"""Base + no-peg legs + square peg + peg survival.
Torso (root) -> Legs on Waist (Peg off by default) -> Base on the legs' Base socket (split by default).
Expect: no peg at the waist; at the base a keyed square peg on the foot, in the middle of the sole,
hole in the (hollow) base; after Apply the peg is really there and every piece is manifold."""
import bpy, bmesh, math, sys
OPEN = '--open' in sys.argv
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d)))
    if not c: fails.append(l)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
ctx = bpy.context; scene = ctx.scene
def mesh_obj(name, fn):
    bm = bmesh.new(); fn(bm); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return ob
def sock(name, parent, mat, t):
    e = bpy.data.objects.new(name, None); scene.collection.objects.link(e); e['ws_type'] = t
    e.parent = parent; e.matrix_world = mat; return e
def child(ob, s):
    ob.parent = s; ob.matrix_parent_inverse = s.matrix_world.inverted()
torso = mesh_obj("Torso", lambda bm: bmesh.ops.create_cube(bm, size=8.0, matrix=Matrix.Translation((0, 0, 14))))
sw = sock("Torso_socket_Waist", torso, Matrix.Translation((0, 0, 10)), "Waist")
# legs: a column standing on a 4 x 7 mm sole at z = 0, off-centre in x
legs = mesh_obj("Legs", lambda bm: bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((2.5, 1.0, 5.0)) @ Matrix.Diagonal((4, 7, 10, 1))))
child(legs, sw)
if OPEN:
    legs.location.z -= 0.5            # the foot sunk into the base: carve
sb = sock("Legs_socket_Base", legs, Matrix.Translation((0, 0, 0)), "Base")
# a 25 mm round base, 3.5 mm tall, hollow underneath (1.5 mm top plate), top at z = 0
base = mesh_obj("Base", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=12.5, radius2=12.5, depth=3.5,
                                                       matrix=Matrix.Translation((0, 0, -1.75))))
cut = mesh_obj("cut", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=11.5, radius2=11.5, depth=4.0,
                                                     matrix=Matrix.Translation((0, 0, -1.5 - 2.0 - 0.01))))
m = base.modifiers.new("c", 'BOOLEAN'); m.object = cut; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'
ctx.view_layer.objects.active = base
with ctx.temp_override(object=base, active_object=base):
    bpy.ops.object.modifier_apply(modifier="c")
bpy.data.objects.remove(cut); ctx.view_layer.update()
if OPEN:                              # punch a face out of the base's underside: not manifold, so Exact
    bm = bmesh.new(); bm.from_mesh(base.data)
    low = min(bm.faces, key=lambda f: f.calc_center_median().z)
    bmesh.ops.delete(bm, geom=[low], context='FACES_ONLY'); bm.to_mesh(base.data); bm.free()
child(base, sb)
for o in scene.objects: o.select_set(False)
torso.select_set(True); ctx.view_layer.objects.active = torso
root, parts = KF.FA_OT_finalise._scan(None, ctx)
items = {it.part: it for it in ctx.window_manager.fa_items}
ck("dialog: legs Peg off by default", not items["Legs"].peg)
ck("dialog: base split + Peg on by default", items["Base"].split and items["Base"].peg)
items["Legs"].split = True
r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True, ident='B', use_exact=OPEN)
print(scene.fa_last_log)
ck("peg profile defaults to Square", scene.fa_peg_profile == 'SQUARE')
ctrls = [o for o in bpy.data.objects if o.get('fa_role') == 'ctrl']
ck("one joint with a peg (the base)", len(ctrls) == 1 and 'Base' in ctrls[0].name, [o.name for o in ctrls])
c = ctrls[0]; F = c.matrix_world.copy(); z = Vector((F[0][2], F[1][2], F[2][2]))
ck("peg on the foot (body side)", c['fa_peg_on'] == 'body', c['fa_peg_on'])
ck("in the middle of the sole", (Vector((F.translation.x, F.translation.y)) - Vector((2.5, 1.0))).length < 0.15, tuple(F.translation))
ck("straight down the leg", abs(abs(z.z) - 1) < 1e-3, tuple(z))
pegs = [o for o in bpy.data.objects if o.get('fa_role') == 'peg']
ck("the peg is the keyed square (5 sides)", len(pegs) == 1 and len(pegs[0].data.vertices) == 15, len(pegs[0].data.vertices) if pegs else None)
lets = [o.name for o in bpy.data.objects if o.get('fa_role') == 'letter']
print(lets)
ck("letters B on legs, base and body", len(lets) == 3 and all('_B_' in n for n in lets), lets)
L = scene.ws_conn_length if scene.ws_conn_size == 'CUSTOM' else None
bpy.ops.fa.apply('EXEC_DEFAULT'); print(scene.fa_last_log)
ck("all manifold (but the open base)", scene.fa_last_log.count(": manifold") == (2 if OPEN else 3), scene.fa_last_log)
pieces = {o.get('fa_src'): o for o in bpy.data.objects if o.get('fa_role') == 'piece'}
def tree(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); t = BVHTree.FromBMesh(bm); bm.free(); return t
def inside(t, p):
    n, pos = 0, Vector(p)
    for _ in range(50):
        loc, nr, i, d = t.ray_cast(pos, Vector((0.123, 0.311, 0.942)).normalized(), 100)
        if loc is None: break
        n += 1; pos = loc + Vector((0.123, 0.311, 0.942)).normalized() * 1e-4
    return n % 2 == 1
pegpt = Vector((2.5, 1.0, -1.0 - (0.5 if OPEN else 0.0)))           # 1 mm below the sole: inside the peg, inside the base's hole
ck("the foot's peg survived (legs solid 1 mm below the sole)", inside(tree(pieces['Legs']), pegpt))
ck("the base has its hole there", not inside(tree(pieces['Base']), pegpt))
print("FAILS:", fails)
