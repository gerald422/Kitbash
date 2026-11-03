import bpy, numpy as np, pickle, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial.transform import Rotation as R
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
out = pickle.load(open('plates.pkl', 'rb')); mp = pickle.load(open('mfplate.pkl', 'rb')); Adj = pickle.load(open('holster_adj.pkl', 'rb'))['Adj']
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'
VW, TW = load(WP); inv_fp, hf = mp['hol']['back (V1/V2/V4)']; VH, TH = load(hf)
for s in 'RL': print(s, 'det W 4A', round(np.linalg.det(mp['res'][('4A', s)]['W'][:3, :3]), 3))
S_wp = np.linalg.inv(mp['res'][('4A', 'L')]['W']) @ out['4A']['L']['F'] @ Adj     # holster socket in WaistPlate file coords
def tf(V, M): return V @ M[:3, :3].T + M[:3, 3]
def bvh(V, T): return BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in T])
def signed(tree, P):
    out_ = []
    for p in P:
        co, n, i, d = tree.find_nearest(Vector(p))
        out_.append(d if (Vector(p) - co).dot(n) >= 0 else -d)
    return np.array(out_)
# overlap with the plate: identical on every leg by construction (pose is relative to the plate)
print('det inv_fp', round(np.linalg.det(inv_fp[:3,:3]),3), 'det S_wp', round(np.linalg.det(S_wp[:3,:3]),3))
Hp = tf(VH, S_wp @ inv_fp); sd = signed(bvh(VW, TW), Hp)
print('holster verts inside plate: %d of %d, deepest %.2f mm' % ((sd < 0).sum(), len(sd), -sd.min()))
for n in range(1, 9):
    a = '%dA' % n; W = mp['res'][(a, 'L')]['W']
    Pp = W @ S_wp @ inv_fp; Pf = out[a]['L']['F'] @ Adj @ inv_fp     # plate-based vs B-seam-based
    H1, H2 = tf(VH, Pp), tf(VH, Pf)
    Q = Pp[:3, :3] @ np.linalg.inv(Pf[:3, :3]); dq = np.linalg.det(Q)
    ang = np.degrees(R.from_matrix(Q / np.cbrt(dq) if dq > 0 else -Q).magnitude()) if dq > 0 else float('nan')
    if dq < 0: print('  %s: mirror between W and seam frame (det W %.2f, det F %.2f)' % (a, np.linalg.det(W[:3, :3]), np.linalg.det(out[a]['L']['F'][:3, :3])))
    VA, TA = load(LD % a + '.stl'); sdl = signed(bvh(VA, TA), H1[::3])
    print('%s: plate-socket vs seam-frame %.2f mm / %.1f deg; holster verts inside legs: %d (deepest %.2f mm)' % (a, np.abs(H1 - H2).max(), ang, (sdl < 0).sum(), -min(sdl.min(), 0)))
pickle.dump({'S_wp': S_wp, 'inv_fp': inv_fp, 'hf': hf}, open('holster_socket.pkl', 'wb'))
