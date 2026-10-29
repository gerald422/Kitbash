"""Run the build on the marine, keep each joint's grid, and plot the joint faces:
footprint (where the two faces meet), the chosen centre (x), the socket (+)."""
import bpy, sys, time, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
bpy.ops.wm.open_mainfile(filepath='/home/claude/review114/ct.blend', load_ui=False)
ctx = bpy.context; scene = ctx.scene; vl = ctx.view_layer
scene.ws_conn_size = 'M'
bpy.data.objects.remove(bpy.data.objects['Weapons-Assault211-BoltPistol-L'])
torso = bpy.data.objects['23-Torso-2']
for o in vl.objects: o.select_set(False)
torso.select_set(True); vl.objects.active = torso
root, parts = KF.FA_OT_finalise._scan(None, ctx)
SPLIT = {'77-Arm-1-R-B', '78-Arm-1-L-A', '1-Helmet-1', '55-JumpPack-1', '29-Legs-2'}
for it in ctx.window_manager.fa_items: it.split = it.part in SPLIT
REC = []
_jp = KF.joint_place
def jp(*a, **k):
    t = time.time(); out = _jp(*a, **k); out['secs'] = time.time() - t; REC.append((a[2].__class__, out)); return out
KF.joint_place = jp
_pl = KF.place_letter
LREC = []
def pl(grid, side, *a, **k):
    t = time.time(); out = _pl(grid, side, *a, **k); LREC.append((grid, side, out, time.time() - t)); return out
KF.place_letter = pl
t = time.time(); r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True, ident='A'); print('build', r, '%.1fs' % (time.time() - t))
print(scene.fa_last_log)
for _c, o in REC: print('joint_place %.2fs grid %s' % (o['secs'], o['grid'].hp.shape))
for g, side, out, secs in LREC: print('letter', side, None if out is None else round(out[2], 2), '%.2fs' % secs)
n = len(REC)
fig, axs = plt.subplots(1, n, figsize=(5 * n, 5))
for k, (_c, o) in enumerate(REC):
    g = o['grid']; ax = axs[k]
    F = g.footprint()
    img = np.where(F, g.hp - g.hb, np.nan)
    ax.imshow(img.T, origin='lower', extent=(g.us[0], g.us[-1], g.vs[0], g.vs[-1]), cmap='viridis', vmin=-1.5, vmax=3)
    c = g.main_face()
    if c: ax.contour(g.us, g.vs, c['mask'].T.astype(float), [0.5], colors='w', linewidths=0.8)
    ax.plot([0], [0], 'r+', ms=14); ax.plot([o['uv'][0]], [o['uv'][1]], 'wx', ms=12)
    ax.set_title(o['how'][-70:] + f"\npeg on {o['peg_on']}, body {o['depth_body']:.1f} piece {o['depth_piece']:.1f}", fontsize=7); ax.set_aspect('equal')
plt.tight_layout(); plt.savefig('/home/claude/finalise/test/centres.png', dpi=80)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/finalise/test/out_centre.blend')
