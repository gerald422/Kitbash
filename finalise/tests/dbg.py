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
import resource
rss = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
hosts = [o for o in bpy.data.objects if o.get('fa_role') == 'host']
for h in hosts:
    for m in h.modifiers: m.show_viewport = False
for h in hosts:
    for m in h.modifiers:
        m.show_viewport = True
        t = time.time(); deps = ctx.evaluated_depsgraph_get(); me = h.evaluated_get(deps).to_mesh()
        print('%-24s %-10s %-9s %-34s faces %7d  %.1fs  rss %.0f MB' % (h.name[:24], m.operation, m.solver, m.object.name[:34], len(me.polygons), time.time() - t, rss()), flush=True)
        h.evaluated_get(deps).to_mesh_clear()
