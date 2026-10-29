import bpy, sys, os, time
sys.path.insert(0, "/home/claude/test"); import rend
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
bpy.ops.wm.open_mainfile(filepath='/home/claude/review114/ct.blend', load_ui=False)
ctx = bpy.context; scene = ctx.scene; vl = ctx.view_layer
scene.ws_conn_shape = 'LONG'; scene.ws_conn_size = 'M'
fails = []
def ck(l, c, d=""):
    print(("  ok   " if c else "  FAIL ") + l + ("" if c else "  " + str(d)))
    if not c: fails.append(l)
torso = bpy.data.objects['23-Torso-2']
for o in vl.objects: o.select_set(False)
torso.select_set(True); vl.objects.active = torso
root, parts = KF.FA_OT_finalise._scan(None, ctx)
wm = ctx.window_manager
print('parts', len(parts), 'bad', [(b.part, b.info) for b in wm.fa_bad])
SPLIT = {'77-Arm-1-R-B', '78-Arm-1-L-A', '1-Helmet-1', '55-JumpPack-1', '29-Legs-2'}
for it in wm.fa_items:
    it.split = it.part in SPLIT
    print('   ' * it.depth, it.label, it.split)
ck("non-manifold pistol listed", any(b.part.startswith('Weapons-Assault211') for b in wm.fa_bad))
try:
    r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True, use_exact=False)
except RuntimeError as e:
    r = {'CANCELLED'}; print('   refused:', e)
ck("refuses without Exact", r == {'CANCELLED'})
# the Exact path is tested on small meshes (t_exact.py): 6 GB here is not enough for Exact on 300k faces
bpy.data.objects.remove(bpy.data.objects['Weapons-Assault211-BoltPistol-L'])
for o in vl.objects: o.select_set(False)
torso.select_set(True); vl.objects.active = torso
root, parts = KF.FA_OT_finalise._scan(None, ctx)
for it in wm.fa_items:
    it.split = it.part in SPLIT
t = time.time()
r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True, use_exact=False)
print('build', r, '%.1fs' % (time.time() - t)); print(scene.fa_last_log)
ck("finalise ran", r == {'FINISHED'})
col = [c for c in bpy.data.collections if c.name.startswith('Finalise')][0]
hosts = [o for o in bpy.data.objects if o.get('fa_role') == 'host']
ck("6 pieces (body + 5)", len(hosts) == 6, [h.name for h in hosts])
for h in hosts:
    print('   %-26s mods %2d  %s' % (h.name, len(h.modifiers), [(m.operation[:3], m.solver[:3], m.object.name[:22]) for m in h.modifiers]))
ck("draft: booleans off", all(not m.show_viewport for h in hosts for m in h.modifiers))
import resource
rss = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
arm = [h for h in hosts if h.name.startswith('77')][0]
for o in vl.objects: o.select_set(False)
arm.select_set(True); vl.objects.active = arm
t = time.time(); bpy.ops.fa.preview('EXEC_DEFAULT'); deps = ctx.evaluated_depsgraph_get()
print('   preview arm %.1fs rss %.0f MB' % (time.time() - t, rss()))
ck("preview turns the arm's booleans on", all(m.show_viewport for m in arm.modifiers))
bpy.ops.fa.preview('EXEC_DEFAULT')
t = time.time()
vl.objects.active = hosts[0]; hosts[0].select_set(True)
r = bpy.ops.fa.apply('EXEC_DEFAULT'); print('apply', r, '%.1fs' % (time.time() - t)); print(scene.fa_last_log)
pieces = [o for o in bpy.data.objects if o.get('fa_role') == 'piece']
ck("6 baked pieces", len(pieces) == 6, [p.name for p in pieces])
left = [o.name for o in bpy.data.objects if o.get('fa_build') and o.get('fa_role') != 'piece']
ck("no cutters left", not left, left[:5])
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/finalise/test/out_fallback.blend')
# exploded render: pieces pulled away from the body along their peg axis
body = [p for p in pieces if p.name.endswith('Body')][0]
import mathutils
for p in pieces:
    if p is body: continue
    c = sum((p.matrix_world @ mathutils.Vector(b) for b in p.bound_box), mathutils.Vector()) / 8
    cb = sum((body.matrix_world @ mathutils.Vector(b) for b in body.bound_box), mathutils.Vector()) / 8
    p.location += (c - cb).normalized() * 9
rend.setup(scene, 800)
cols = [rend.GREY if p is body else rend.BLUE for p in pieces]
rend.render(scene, "/home/claude/finalise/test", "fallback", pieces, {"front": (0.3, 1, 0.2), "back": (-0.3, -1, 0.3), "side": (1, 0.1, 0.2)}, cols)
print("FAILS:", fails)
