"""Peg placement on a hollow body: a post (piece) slides up into a deep recess under a thin ceiling,
socket off-centre. Expect: axis straight along the post, peg in the middle of the post's top, peg on the
body (ceiling too thin for the hole), hole in the post; one letter each; both manifold after Apply.
Then the same with a thick ceiling: peg on the piece. Then 'Always the piece' forces the piece."""
import bpy, bmesh, math
from mathutils import Matrix, Vector
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d)))
    if not c: fails.append(l)
def setup(recess_depth):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.preferences.addon_enable(module="part_sockets")
    bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
    bpy.ops.preferences.addon_enable(module="kitbash_finalise")
    import kitbash_finalise as KF
    ctx = bpy.context; scene = ctx.scene
    def mesh_obj(name, fn):
        bm = bmesh.new(); fn(bm); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return ob
    body = mesh_obj("Torso", lambda bm: bmesh.ops.create_cube(bm, size=10.0))
    cut = mesh_obj("cut", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=3.2, radius2=3.2,
                                                         depth=recess_depth * 2, matrix=Matrix.Translation((0, 0, -5))))
    m = body.modifiers.new("c", 'BOOLEAN'); m.object = cut; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'
    ctx.view_layer.objects.active = body
    with ctx.temp_override(object=body, active_object=body):
        bpy.ops.object.modifier_apply(modifier="c")
    bpy.data.objects.remove(cut)
    ctx.view_layer.update()
    ceiling = -5 + recess_depth
    sk = bpy.data.objects.new("Torso_socket_Waist", None); scene.collection.objects.link(sk); sk['ws_type'] = 'Waist'
    sk.parent = body; sk.matrix_world = Matrix.Translation((1.5, 0.8, ceiling - 2.0))     # off-centre on purpose
    post = mesh_obj("Legs", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=3.2, radius2=3.2, depth=10,
                                                          matrix=Matrix.Translation((0, 0, ceiling - 2.0 - 5.0))))
    post.parent = sk; post.matrix_parent_inverse = sk.matrix_world.inverted()
    for o in scene.objects: o.select_set(False)
    body.select_set(True); ctx.view_layer.objects.active = body
    return KF, ctx, body, post
for recess, side, want in ((8.8, 'AUTO', 'body'), (5.0, 'AUTO', 'piece'), (8.8, 'PIECE', 'piece')):
    print(f"--- recess {recess}, peg side {side}")
    KF, ctx, body, post = setup(recess)
    scene = ctx.scene; scene.fa_peg_side = side
    root, parts = KF.FA_OT_finalise._scan(None, ctx)
    for it in ctx.window_manager.fa_items: it.split = True; it.peg = True   # a Waist joint: Peg is off by default
    r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True, ident='Q')
    print(scene.fa_last_log)
    c = [o for o in bpy.data.objects if o.get('fa_role') == 'ctrl'][0]
    F = c.matrix_world; z = Vector((F[0][2], F[1][2], F[2][2]))
    ck("axis straight along the post", abs(abs(z.z) - 1) < 1e-3, tuple(z))
    ck("peg in the middle of the post's top", Vector((F.translation.x, F.translation.y)).length < 0.15, tuple(F.translation))
    ck(f"peg on the {want}", c['fa_peg_on'] == want, c['fa_peg_on'])
    lets = [o.name for o in bpy.data.objects if o.get('fa_role') == 'letter']
    ck("two letters, both Q", len(lets) == 2 and all('_Q_' in n for n in lets), lets)
    Lc, side = c['fa_L'], c['fa_peg_on']; mid = F.translation - z * (Lc * 0.5)
    bpy.ops.fa.apply('EXEC_DEFAULT'); print(scene.fa_last_log)
    ck("both manifold", scene.fa_last_log.count(": manifold") == 2, scene.fa_last_log)
    import bmesh as bm_
    from mathutils.bvhtree import BVHTree
    def inside(o, p):
        b = bm_.new(); b.from_mesh(o.data); b.transform(o.matrix_world); t = BVHTree.FromBMesh(b); b.free()
        d = Vector((0.123, 0.311, 0.942)).normalized(); n, pos = 0, Vector(p)
        for _ in range(60):
            loc, nr, i, dd = t.ray_cast(pos, d, 200)
            if loc is None: break
            n += 1; pos = loc + d * 1e-4
        return n % 2 == 1
    pcs = {o.get('fa_src'): o for o in bpy.data.objects if o.get('fa_role') == 'piece'}
    own, oth = (pcs['Legs'], pcs['Torso']) if side == 'piece' else (pcs['Torso'], pcs['Legs'])
    ck("the peg survived Apply", inside(own, mid))
    ck("its hole is there", not inside(oth, mid))
print("FAILS:", fails)
