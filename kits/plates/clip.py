import bpy, numpy as np, pickle, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
mp = pickle.load(open('mfplate.pkl', 'rb')); hs = pickle.load(open('holster_socket.pkl', 'rb')); VH, TH = load(hs['hf'])
def inside(tree, p, dirs=((1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0))):
    votes = 0
    for d in dirs:
        o, d, k = Vector(p), Vector(d), 0
        while True:
            hit = tree.ray_cast(o, d)
            if hit[0] is None: break
            k += 1; o = hit[0] + d * 1e-4
        votes += k % 2
    return votes >= 3
for n in range(1, 9):
    a = '%dA' % n; VA, TA = load(LD % a + '.stl'); tree = BVHTree.FromPolygons([tuple(v) for v in VA], [tuple(t) for t in TA])
    P = mp['res'][(a, 'L')]['W'] @ hs['S_wp'] @ hs['inv_fp']; H = VH @ P[:3, :3].T + P[:3, 3]
    ins = np.array([inside(tree, p) for p in H[::2]])
    if ins.any():
        Hi = H[::2][ins]; d = np.array([tree.find_nearest(Vector(p))[3] for p in Hi])
        print('%s: %d holster verts inside the legs, deepest %.2f mm' % (a, ins.sum(), d.max()))
    else: print('%s: clear of the legs' % a)
