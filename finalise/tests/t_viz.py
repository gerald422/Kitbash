"""Build + apply on Josh's Mar Fil marine, then slice every joint through its peg axis."""
import bpy, sys, time, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
bpy.ops.wm.open_mainfile(filepath='/home/claude/review114/ct.blend', load_ui=False)
ctx = bpy.context; scene = ctx.scene; vl = ctx.view_layer
scene.ws_conn_shape = 'DISC'; scene.ws_conn_size = 'M'   # Disc in the scene: Finalise still uses the Long peg
bpy.data.objects.remove(bpy.data.objects['Weapons-Assault211-BoltPistol-L'])
torso = bpy.data.objects['23-Torso-2']
for o in vl.objects: o.select_set(False)
torso.select_set(True); vl.objects.active = torso
root, parts = KF.FA_OT_finalise._scan(None, ctx)
SPLIT = set(sys.argv[sys.argv.index('--') + 1].split(',')) if '--' in sys.argv else {'77-Arm-1-R-B', '78-Arm-1-L-A', '1-Helmet-1', '55-JumpPack-1', '29-Legs-2'}
for it in ctx.window_manager.fa_items: it.split = it.part in SPLIT
t = time.time(); r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True); print('build', r, '%.1fs' % (time.time() - t))
print(scene.fa_last_log)
ctrls = {o['fa_letter']: (o.matrix_world.copy(), o['fa_piece'], o['fa_body']) for o in bpy.data.objects if o.get('fa_role') == 'ctrl'}
t = time.time(); bpy.ops.fa.apply('EXEC_DEFAULT'); print('apply %.1fs' % (time.time() - t)); print(scene.fa_last_log)
pieces = {o.get('fa_src'): o for o in bpy.data.objects if o.get('fa_role') == 'piece'}
deps = ctx.evaluated_depsgraph_get()
def tris(ob):
    me = ob.evaluated_get(deps).to_mesh(); me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    t = np.empty(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get('vertices', t); t = t.reshape(-1, 3)
    M = np.array(ob.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]; return co[t]
def section(T, n, d):
    s = T @ n - d; m = ~((s > 0).all(1) | (s <= 0).all(1)); T, s = T[m], s[m]; out = []
    for tri, sd in zip(T, s):
        pts = []
        for i in range(3):
            j = (i + 1) % 3
            if (sd[i] > 0) != (sd[j] > 0):
                tt = sd[i] / (sd[i] - sd[j]); pts.append(tri[i] + tt * (tri[j] - tri[i]))
        if len(pts) == 2: out.append(pts)
    return np.array(out)
keys = sorted(ctrls)
fig, axs = plt.subplots(2, len(keys), figsize=(5.5 * len(keys), 11))
axs = np.atleast_2d(axs).reshape(2, -1)
for k, tag in enumerate(keys):
    F, pname, bname = ctrls[tag]; F = np.array(F)
    o, x, y, z = F[:3, 3], F[:3, 0], F[:3, 1], F[:3, 2]
    body = [p for p in pieces.values() if p.name.endswith('Body')][0]
    piece = [p for p in pieces.values() if p.name.startswith(bpy.data.objects[0].name[:0]) and (' ' + tag + ' ') in p.name][0]
    for row, (n, u) in enumerate([(y, x), (x, y)]):      # two planes through the axis
        ax = axs[row, k]
        for ob, colr in ((body, 'k'), (piece, 'tab:orange')):
            S = section(tris(ob), n, n @ o)
            for a, b in S:
                ax.plot([(a - o) @ u, (b - o) @ u], [(a - o) @ z, (b - o) @ z], colr, lw=0.7)
        ax.axvline(0, color='r', lw=0.5, ls='--'); ax.set_xlim(-6, 6); ax.set_ylim(-5, 5); ax.set_aspect('equal'); ax.grid(alpha=0.3)
        ax.set_title(f"{tag}: {piece.name.split(' ', 3)[-1]}  ({'xz' if row == 0 else 'yz'} plane, z = pull-off)")
plt.tight_layout(); plt.savefig('/home/claude/finalise/test/joints.png', dpi=90)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/finalise/test/out_viz.blend')
# close-ups of the mating faces, looking down the peg axis
from mathutils import Matrix, Vector
cam = bpy.data.objects.get('cam') or bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
if cam.name not in scene.collection.objects: scene.collection.objects.link(cam)
scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 11; cam.data.clip_end = 200
scene.render.engine = 'BLENDER_WORKBENCH'; scene.display.shading.light = 'STUDIO'; scene.display.shading.show_cavity = True
scene.display.shading.color_type = 'SINGLE'
scene.render.resolution_x = scene.render.resolution_y = 500
from PIL import Image, ImageDraw
tiles = []
for tag in keys:
    F = ctrls[tag][0]; o = F.translation; z = Vector((F[0][2], F[1][2], F[2][2])); x = Vector((F[0][0], F[1][0], F[2][0]))
    body = [p for p in pieces.values() if p.name.endswith('Body')][0]
    piece = [p for p in pieces.values() if (' ' + tag + ' ') in p.name][0]
    for who, ob, d in (('body', body, z), ('piece', piece, -z)):
        for o2 in bpy.data.objects:
            if o2.type == 'MESH': o2.hide_render = o2 is not ob
        up = x
        zz = d.normalized(); xx = up.cross(zz).normalized(); yy = zz.cross(xx)
        cam.matrix_world = Matrix((xx, yy, zz)).transposed().to_4x4(); cam.location = o + d * 30
        f = f'/home/claude/finalise/test/face_{tag}_{who}.png'; scene.render.filepath = f
        bpy.ops.render.render(write_still=True)
        im = Image.open(f).convert('RGB'); ImageDraw.Draw(im).text((6, 6), f'{tag} {who}', fill='red'); tiles.append(im)
W = len(keys)
g = Image.new('RGB', (500 * W, 1000), 'white')
for k, im in enumerate(tiles): g.paste(im, ((k // 2) * 500, (k % 2) * 500))
g.save('/home/claude/finalise/test/faces.jpg', quality=88)
