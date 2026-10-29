import bpy, numpy as np, sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
bpy.ops.wm.open_mainfile(filepath='/home/claude/review114/ct.blend', load_ui=False)
deps = bpy.context.evaluated_depsgraph_get()
def tris(ob):
    me = ob.evaluated_get(deps).to_mesh(); me.calc_loop_triangles()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    t = np.empty(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get('vertices', t); t = t.reshape(-1, 3)
    M = np.array(ob.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    return co[t]
def section(T, n, d):
    s = T @ n - d; segs = []
    for tri, sd in zip(T, s):
        pos = sd > 0
        if pos.all() or (~pos).all(): continue
        pts = []
        for i in range(3):
            j = (i + 1) % 3
            if (sd[i] > 0) != (sd[j] > 0):
                t = sd[i] / (sd[i] - sd[j]); pts.append(tri[i] + t * (tri[j] - tri[i]))
        if len(pts) == 2: segs.append(pts)
    return np.array(segs)
O = bpy.data.objects
cases = [('arm R  y=-0.64 (x right, z up)', ['23-Torso-2', '77-Arm-1-R-B'], np.array([0, 1., 0]), -0.64, (0, 2), (2, 10, -4, 5)),
         ('waist x=0 (y fwd, z up)', ['23-Torso-2', '29-Legs-2'], np.array([1., 0, 0]), 0.0, (1, 2), (-8, 8, -8, 3)),
         ('neck x=0 (y fwd, z up)', ['23-Torso-2', '1-Helmet-1'], np.array([1., 0, 0]), 0.0, (1, 2), (-6, 6, -2, 8)),
         ('pack x=0 (y fwd, z up)', ['23-Torso-2', '55-JumpPack-1'], np.array([1., 0, 0]), 0.0, (1, 2), (-12, 2, -4, 8))]
fig, axs = plt.subplots(1, 4, figsize=(22, 6))
for ax, (title, obs, n, d, (i, j), lim) in zip(axs, cases):
    for ob, colr in zip(obs, ['k', 'tab:orange']):
        S = section(tris(O[ob]), n, d)
        for a, b in S: ax.plot([a[i], b[i]], [a[j], b[j]], colr, lw=0.6)
    s = {'arm': '23-Torso-2_socket_Shoulder R', 'waist': '23-Torso-2_socket_Waist', 'neck': '23-Torso-2_socket_Neck', 'pack': '23-Torso-2_socket_Back'}[title.split()[0]]
    p = np.array(O[s].matrix_world.translation); ax.plot(p[i], p[j], 'r+', ms=12)
    ax.set_title(title); ax.set_aspect('equal'); ax.set_xlim(lim[0], lim[1]); ax.set_ylim(lim[2], lim[3]); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig('/home/claude/finalise/test/slices.png', dpi=110)
