import bpy, numpy as np, pickle, json
from mathutils import Matrix
from scipy.spatial import cKDTree
exec(open('rtab.py').read().split("bpy.ops.wm.read_factory_settings")[0])
bpy.ops.wm.read_factory_settings(use_empty=True)
def thin(V, T, g=0.1):
    key = np.floor(V / g).astype(np.int64); _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
    T2 = inv[T]; ok = (T2[:, 0] != T2[:, 1]) & (T2[:, 1] != T2[:, 2]) & (T2[:, 0] != T2[:, 2]); return V[first], T2[ok]
jobs = [('4A', LD % '4A', 1), ('6A', LD % '6A', 2), ('8A', LD % '8A', 4), ('S2', LS % 2, 5)]
ref = {}
for i, (a, path, loin) in enumerate(jobs):
    VA, TA = load(path + '.stl'); sc = json.load(open(path + '.sockets.json')); O = np.eye(4); O[0, 3] = 40 * i; M = O @ S_WAIST @ M16(sc['fits']['Waist'])
    Aw = VA[TA]; c = np.cross(Aw[:, 1] - Aw[:, 0], Aw[:, 2] - Aw[:, 0]); ar = np.linalg.norm(c, axis=1); rng = np.random.default_rng(0)
    k = rng.choice(len(TA), 300000, p=ar / ar.sum()); u, w = rng.random(300000), rng.random(300000); f = u + w > 1; u[f], w[f] = 1 - u[f], 1 - w[f]
    S = tf(Aw[k, 0] + (Aw[k, 1] - Aw[k, 0]) * u[:, None] + (Aw[k, 2] - Aw[k, 0]) * w[:, None], M); N = (c[k] / ar[k, None]) @ M[:3, :3].T; tree = cKDTree(S)
    lab = {'S2': 'Standing 2'}.get(a, a)
    cen = tf(VA[TA].mean(1), M); keep = np.linalg.norm(cen - tf(((VB.min(0) + VB.max(0)) / 2)[None], M @ BS['pose'][a])[0], axis=1) < 17      # legs cropped around the buckle (file size)
    TK = TA[keep]; used, inv = np.unique(TK, return_inverse=True)
    mesh('Legs ' + lab + ' (cropped)', *thin(VA[used], inv.reshape(-1, 3), 0.08), M); mesh('Buckle ' + lab, VB, TB, M @ BS['pose'][a])
    VL, TL = load(CBL % loin + '.stl'); fit = M16(json.load(open(CBL % loin + '.sockets.json'))['fits']['Belt Front'])
    A = M @ BS['pose'][a] @ BS['TAB']; P0, t = settle(samples(VL, TL, 20000), A @ fit, A, tree, S, N)
    # bake so the object origin sits on the buckle's tabard spot, axes = world
    piv = A[:3, 3] + A[:3, 2] * t; Vw = VL @ P0[:3, :3].T + P0[:3, 3]; T0 = np.eye(4); T0[:3, 3] = piv
    Vt, Tt = thin(Vw - piv, TL); ob = mesh('Tabard %d on %s (move me)' % (loin, lab), Vt, Tt, T0); ref[ob.name] = dict(a=a, loin=loin, P0=P0, piv=piv, M=M, A=A)
pickle.dump(ref, open('tab_blend_ref.pkl', 'wb'))
bpy.context.scene.unit_settings.scale_length = 0.001; bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
bpy.ops.wm.save_as_mainfile(filepath='/mnt/user-data/outputs/plates-2026-11-03/tabard check.blend', compress=True); print('saved')
