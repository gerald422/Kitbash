"""Shoulder pad plug (0.3.4). A dome 'arm' with a pad shell over it on a Pad socket, printed as one piece:
1. the pad floats 0.5 mm over the arm: a plug is made under the crown (inside the rim), the piece comes out one
   manifold shell and the pad isn't moved;
2. the pad cuts into the arm and carries an extra overlapping stud shell (as some makers' STLs do): no plug, the
   stud is joined, one manifold shell;
3. the plug switched off: the floating pad stays loose and Apply reports separate shells."""
import bpy, bmesh, math
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


def solid(name, fn):
    bm = bmesh.new(); fn(bm); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return ob


def bake(ob, other, op):
    m = ob.modifiers.new("b", 'BOOLEAN'); m.operation, m.object, m.solver = op, other, 'MANIFOLD'
    deps = ctx.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    ob.modifiers.remove(m); ob.data = me; bpy.data.objects.remove(other)


def model(tag, x, inner, stud):
    arm = solid(f"{tag} Arm", lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=4.0))
    post = solid("post", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=3.0, radius2=3.0,
                                                          depth=10.0, matrix=Matrix.Translation((0, 0, -5))))
    bake(arm, post, 'UNION')
    pad = solid(f"{tag} Pad", lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=6.0))
    hole = solid("in", lambda bm: bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=inner))
    bake(pad, hole, 'DIFFERENCE')
    cut = solid("cut", lambda bm: bmesh.ops.create_cube(bm, size=20.0, matrix=Matrix.Translation((0, 0, -11.5))))
    bake(pad, cut, 'DIFFERENCE')
    if stud:   # a second shell overlapping the pad's top, left as its own shell in the mesh
        bm = bmesh.new(); bm.from_mesh(pad.data)
        bmesh.ops.create_cube(bm, size=1.5, matrix=Matrix.Translation((1.5, 0, 5.9)))
        bm.to_mesh(pad.data); bm.free()
    for o in (arm, pad):
        o.matrix_world = Matrix.Translation((x, 0, 0))
    s = bpy.data.objects.new(f"WS_{tag}_pad", None); scene.collection.objects.link(s); s["ws_type"] = "Pad R"
    s.parent = arm; s.matrix_world = Matrix.Translation((x, 0, 4.0))
    mw = pad.matrix_world.copy(); pad.parent = s; pad.matrix_parent_inverse = s.matrix_world.inverted(); pad.matrix_world = mw
    vl.update()
    return arm, pad


def run(arm, plug):
    for o in vl.objects: o.select_set(False)
    vl.objects.active = arm; arm.select_set(True)
    wm = ctx.window_manager; wm.fa_items.clear(); wm.fa_bad.clear(); wm.fa_root = ""   # no dialog: scan this model
    bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=False, pad_plug=plug, letters=False)
    log = scene.fa_last_log
    col = KF.current_build(ctx)
    plugs = [[o.matrix_world @ v.co for v in o.data.vertices]        # read before Apply deletes them
             for o in KF.build_objects(col[KF.TAG]) if o.get(KF.ROLE) == "plug"]
    host = [o for o in KF.build_objects(col[KF.TAG]) if o.get(KF.ROLE) == "host"][0]
    for o in vl.objects: o.select_set(False)
    vl.objects.active = host; host.select_set(True)
    bpy.ops.fa.apply()
    return log, plugs, host, scene.fa_last_log


def shells(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); _s, k = KF.shells_of(bm); bm.free(); return k


# 1. floating pad: plug, one shell, pad not moved, plug inside the rim
arm, pad = model("A", 0.0, 4.5, False)
before = pad.matrix_world.copy()
log, plugs, host, alog = run(arm, True)
ck("floating pad: plug made", "plug under the crown" in log and len(plugs) == 1, log)
if plugs:
    P = plugs[0]
    ck("plug under the crown (within 2.6 mm of the axis)", max(math.hypot(p.x, p.y) for p in P) < 2.6,
       max(math.hypot(p.x, p.y) for p in P))
    ck("plug inside the pad (below its outside)", max(p.length for p in P) < 6.0, max(p.length for p in P))
ck("floating pad: piece manifold, one shell", "manifold" in alog and "separate" not in alog and shells(host) == 1,
   (alog, shells(host)))
ck("pad not moved", (pad.matrix_world.translation - before.translation).length < 1e-6)

# 2. pad cutting into the arm, with an overlapping stud shell: no plug, joined
arm, pad = model("B", 20.0, 3.8, True)
log, plugs, host, alog = run(arm, True)
ck("touching pad: no plug", not plugs and "plug" not in log, log)
ck("stud shell joined", "overlapping shells in the file, joined" in log, log)
ck("touching pad: piece manifold, one shell", "separate" not in alog and shells(host) == 1, (alog, shells(host)))

# 3. plug off: the floating pad stays loose and is reported
arm, pad = model("C", 40.0, 4.5, False)
log, plugs, host, alog = run(arm, False)
ck("plug off: no plug", not plugs, log)
ck("plug off: separate shells reported", "separate shells" in alog and shells(host) == 2, (alog, shells(host)))
print("FAILS:", fails)
