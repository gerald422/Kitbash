"""Build + apply on Josh's marine; slice every joint through its peg axis (joints.png) and
render both mating faces looking down the axis (faces.jpg)."""
import bpy, sys, time, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
from mathutils import Matrix, Vector
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
t = time.time(); r = bpy.ops.fa.finalise('EXEC_DEFAULT', subassemblies=True, ident='A'); print('build', r, '%.1fs' % (time.time() - t))
print(scene.fa_last_log)
ctrls = []
for o in bpy.data.objects:
    if o.get('fa_role') == 'ctrl':
        F = o.matrix_world.copy(); z = Vector((F[0][2], F[1][2], F[2][2]))
        pull = z if o['fa_peg_on'] == 'piece' else -z
        ctrls.append((o.name.split('_')[2], F, pull, bpy.data.objects[o['fa_piece']]['fa_src'], o['fa_peg_on'], o['fa_L']))
ctrls.sort()
t = time.time(); bpy.ops.fa.apply('EXEC_DEFAULT'); print('apply %.1fs' % (time.time() - t)); print(scene.fa_last_log)
pieces = {o.get('fa_src'): o for o in bpy.data.objects if o.get('fa_role') == 'piece'}
body = [o for o in pieces.values() if o.get('fa_kind') == 'body'][0]
import bmesh
from mathutils.bvhtree import BVHTree
def tree(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world); t = BVHTree.FromBMesh(bm); bm.free(); return t
def inside(t, p):
    d = Vector((0.123, 0.311, 0.942)).normalized(); n, pos = 0, Vector(p)
    for _ in range(80):
        loc, nr, i, dd = t.ray_cast(pos, d, 200)
        if loc is None: break
        n += 1; pos = loc + d * 1e-4
    return n % 2 == 1
for tag, F, pull, src, side, L in ctrls:
    z = Vector((F[0][2], F[1][2], F[2][2])); mid = F.translation - z * (L * 0.5)
    own, oth = (pieces[src], body) if side == 'piece' else (body, pieces[src])
    print('PEGCHECK', tag, src, 'peg on', side, 'peg there:', inside(tree(own), mid), '| hole there:', not inside(tree(oth), mid))
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
TB = tris(body)
fig, axs = plt.subplots(2, len(ctrls), figsize=(5.5 * len(ctrls), 11))
for k, (tag, F, pull, src, side, L) in enumerate(ctrls):
    F = np.array(F); o, x, y = F[:3, 3], F[:3, 0], F[:3, 1]; z = np.array(pull)
    piece = pieces[src]; TP = tris(piece)
    for row, (n, u) in enumerate([(y, x), (x, y)]):
        ax = axs[row, k]
        for T, colr in ((TB, 'k'), (TP, 'tab:orange')):
            for a, b in section(T, n, n @ o):
                ax.plot([(a - o) @ u, (b - o) @ u], [(a - o) @ z, (b - o) @ z], colr, lw=0.7)
        ax.axvline(0, color='r', lw=0.5, ls='--'); ax.set_xlim(-7, 7); ax.set_ylim(-6, 6); ax.set_aspect('equal'); ax.grid(alpha=0.3)
        ax.set_title(f"{tag}: {src} (peg on {side}), up = pull-off", fontsize=9)
plt.tight_layout(); plt.savefig('/home/claude/finalise/test/joints.png', dpi=80)
bpy.ops.wm.save_as_mainfile(filepath='/home/claude/finalise/test/out_viz.blend')
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam)
scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 12; cam.data.clip_end = 200
scene.render.engine = 'BLENDER_WORKBENCH'; scene.display.shading.light = 'STUDIO'; scene.display.shading.show_cavity = True
scene.display.shading.color_type = 'SINGLE'
scene.render.resolution_x = scene.render.resolution_y = 500
from PIL import Image, ImageDraw
tiles = []
for tag, F, pull, src, side, L in ctrls:
    o = F.translation; x = Vector((F[0][0], F[1][0], F[2][0]))
    for who, ob, d in (('body', body, pull), ('piece', pieces[src], -pull)):
        for o2 in bpy.data.objects:
            if o2.type == 'MESH': o2.hide_render = o2 is not ob
        zz = d.normalized(); xx = x.cross(zz).normalized(); yy = zz.cross(xx)
        cam.matrix_world = Matrix((xx, yy, zz)).transposed().to_4x4(); cam.location = o + d * 30
        f = f'/home/claude/finalise/test/face_{tag}_{who}.png'; scene.render.filepath = f
        bpy.ops.render.render(write_still=True)
        im = Image.open(f).convert('RGB'); ImageDraw.Draw(im).text((6, 6), f'{tag} {who}: {src}', fill='red'); tiles.append(im)
g = Image.new('RGB', (500 * len(ctrls), 1000), 'white')
for k, im in enumerate(tiles): g.paste(im, ((k // 2) * 500, (k % 2) * 500))
g.save('/home/claude/finalise/test/faces.jpg', quality=88)
