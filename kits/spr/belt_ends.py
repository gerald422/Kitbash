import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real'); import stlcache, fitlib as F
from scipy.spatial import ConvexHull
U = "/mnt/user-data/uploads/new cults/Springles/"
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
def ends(V):
    H = V[ConvexHull(V).vertices]
    D = np.linalg.norm(H[:, None] - H[None], axis=2); i, j = np.unravel_index(np.argmax(D), D.shape)
    return H[i], H[j]
def crop(V, T, c, r, out):
    cen = V[T].mean(1); k = np.linalg.norm(cen - c, axis=1) < r; T2 = T[k]; u, inv = np.unique(T2, return_inverse=True)
    np.savez(out, V=V[u].astype(np.float32), T=inv.reshape(-1, 3).astype(np.int32)); return out
models = []
for i, f in enumerate(["heavy weapons/las cannon/las cannon belt 1.stl", "heavy weapons/heavy bolter/heavy bolter belt 1.stl"]):
    V, T = stlcache.load(U + f); a, b = ends(V)
    print(f, "ends", a.round(2), b.round(2), "dist %.1f" % np.linalg.norm(a - b))
    for j, e in enumerate((a, b)):
        p = crop(V, T, e, 4.0, SCR + "be%d%d.npz" % (i, j))
        models.append(dict(name="be%d%d" % (i, j), items=[[p, np.eye(4).ravel().tolist(), [0.8, 0.7, 0.55, 1]]]))
json.dump({"out": "/home/claude/kits/spr/rbe", "res": 240, "pad": 1.1, "models": models, "views": {"py": [0, 1, 0.2], "my": [0, -1, 0.2], "px": [1, 0.1, 0.2], "mx": [-1, 0.1, 0.2]}}, open("j_be.json", "w"))
