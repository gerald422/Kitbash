import bpy, sys, os, time, resource
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
bpy.ops.wm.open_mainfile(filepath='/home/claude/review114/ct.blend', load_ui=False)
ctx = bpy.context; scene = ctx.scene; vl = ctx.view_layer
scene.ws_conn_shape = 'LONG'; scene.ws_conn_size = 'M'
rss = lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
bpy.data.objects.remove(bpy.data.objects['Weapons-Assault211-BoltPistol-L'])
torso = bpy.data.objects['23-Torso-2']
orig = KF.add_booleans
def quiet(ctx, host, cutters, operation, solver, use_hops):
    n0 = len(host.modifiers); r = orig(ctx, host, cutters, operation, solver, use_hops)
    for m in host.modifiers[n0:]: m.show_viewport = False
    return r
KF.add_booleans = quiet
parts = KF.assembly(torso)
SPLIT = {'77-Arm-1-R-B', '78-Arm-1-L-A', '1-Helmet-1', '55-JumpPack-1', '29-Legs-2'}
splits = {p for p in parts if p.name in SPLIT}
log = []
opts = dict(use_hops=False, carve=True, letters=True, letter_size=1.2, letter_depth=0.2)
t = time.time(); col, how = KF.build(ctx, torso, parts, splits, set(), opts, log); print('build %.1fs rss %.0f' % (time.time() - t, rss()), flush=True)
hosts = [o for o in bpy.data.objects if o.get('fa_role') == 'host']
for h in hosts:
    for m in h.modifiers:
        m.show_viewport = True
        t = time.time(); deps = ctx.evaluated_depsgraph_get(); me = h.evaluated_get(deps).to_mesh()
        print('%-24s %-10s %-9s %-34s faces %7d  %.1fs  rss %.0f MB' % (h.name[:24], m.operation, m.solver, m.object.name[:34], len(me.polygons), time.time() - t, rss()), flush=True)
        h.evaluated_get(deps).to_mesh_clear()
