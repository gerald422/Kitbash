import bpy, numpy as np, math
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.preferences.addon_install(filepath="/home/claude/finalise/kitbash_finalise.py", overwrite=True)
bpy.ops.preferences.addon_enable(module="kitbash_finalise")
import kitbash_finalise as KF
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath='/home/claude/review114/ct.blend', load_ui=False)
ctx = bpy.context; deps = ctx.evaluated_depsgraph_get()
O = bpy.data.objects
torso = O['23-Torso-2']
J = [('29-Legs-2', 'Waist'), ('1-Helmet-1', 'Neck'), ('55-JumpPack-1', 'Back')]
rt = KF.Ray(torso, deps)
fig, axs = plt.subplots(2, 3, figsize=(15, 10))
for k, (pn, nm) in enumerate(J):
    s = O[pn]; sock = KF.joint_socket(s); rs = KF.Ray(s, deps)
    pc = s.matrix_world @ (sum((Vector(v) for v in s.bound_box), Vector()) / 8.0)
    jf = KF.joint_place(sock, rt, rs, KF.Surf([rt]), KF.Surf([rs]), pc, 1.25)
    g = jf['grid']; z = g.z
    D = np.full(g.hb.shape, np.nan)
    for i in range(0, len(g.us), 2):
        for j in range(0, len(g.vs), 2):
            if np.isnan(g.hb[i, j]): continue
            P = g.point(g.us[i], g.vs[j], g.hb[i, j])
            D[i, j] = KF._depth(rt, P, -z)
    ax = axs[0, k]
    im = ax.imshow(D[::2, ::2].T, origin='lower', extent=(g.us[0], g.us[-1], g.vs[0], g.vs[-1]), vmin=0, vmax=6)
    plt.colorbar(im, ax=ax); ax.plot([0], [0], 'r+'); ax.plot([jf['uv'][0]], [jf['uv'][1]], 'wx')
    ax.set_title(f'{nm}: torso depth along -z from its face')
    # section through the centre along u
    ax = axs[1, k]
    uc, vc = jf['uv']
    from mathutils import Vector as V
    # torso & piece sections in plane spanned by x,z through centre
    def sect(ob):
        me = ob.evaluated_get(deps).to_mesh(); me.calc_loop_triangles()
        co = np.array([ob.matrix_world @ v.co for v in me.vertices]); t = np.array([lt.vertices[:] for lt in me.loop_triangles])
        T = co[t]; n = np.array(g.y); d = n @ np.array(g.point(uc, vc))
        sd = T @ n - d; m = ~((sd > 0).all(1) | (sd <= 0).all(1)); out = []
        for tri, sdd in zip(T[m], sd[m]):
            pts = []
            for a in range(3):
                b = (a + 1) % 3
                if (sdd[a] > 0) != (sdd[b] > 0):
                    tt = sdd[a] / (sdd[a] - sdd[b]); pts.append(tri[a] + tt * (tri[b] - tri[a]))
            if len(pts) == 2: out.append(pts)
        ob.evaluated_get(deps).to_mesh_clear(); return np.array(out)
    Oc = np.array(g.o)
    for ob, c in ((torso, 'k'), (s, 'tab:orange')):
        for a, b in sect(ob):
            ax.plot([(a - Oc) @ np.array(g.x), (b - Oc) @ np.array(g.x)], [(a - Oc) @ np.array(z), (b - Oc) @ np.array(z)], c, lw=0.6)
    ax.axvline(uc, color='r', lw=0.5); ax.axvline(0, color='b', lw=0.5, ls='--')
    ax.set_xlim(-8, 8); ax.set_ylim(-8, 8); ax.set_aspect('equal'); ax.set_title(f'{nm} section (z up = pull-off), depth {jf["depth"]:.2f}')
    print(nm, 'uv', jf['uv'], 'depth', jf['depth'], 'frame o', tuple(round(x, 2) for x in jf['frame'].translation))
plt.tight_layout(); plt.savefig('/home/claude/finalise/test/depth.png', dpi=75)
