import sys, numpy as np, collections
sys.path.insert(0, '/home/claude/kits/cr'); import stlcache
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
def sharp_edges(V, T, ang=25):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]); fn /= np.linalg.norm(fn, axis=1)[:, None] + 1e-12
    E = np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]; F = np.tile(np.arange(len(T)), 3)
    Es = np.sort(E, 1); key = Es[:, 0].astype(np.int64) * (len(V) + 1) + Es[:, 1]
    o = np.argsort(key); key, F, Es = key[o], F[o], Es[o]
    same = key[1:] == key[:-1]; i = np.where(same)[0]
    d = np.degrees(np.arccos(np.clip((fn[F[i]] * fn[F[i + 1]]).sum(1), -1, 1)))
    k = d > ang
    return Es[i[k]], d[k]
z = np.load(SCR + "hand_grip_big.npz"); V, T = z["V"].astype(float), z["T"]
E, d = sharp_edges(V, T, 20)
apex = np.array([-52.8, -63.1, 6.1])
M = V[E].mean(1); k = np.linalg.norm(M - apex, axis=1) < 3.0
print("sharp edges near apex", k.sum())
P = V[np.unique(E[k])]
for p, dd in sorted(zip(map(tuple, M[k].round(2)), d[k].round(0)))[:0]: print(p, dd)
# cluster by distance along the guessed axis
a = np.array([-1.0, -0.15, 0]); a /= np.linalg.norm(a)
h = (P - apex) @ a; lat = np.linalg.norm(P - apex - np.outer(h, a), axis=1)
for hb in np.arange(-2.5, 0.5, 0.1):
    q = (h > hb) & (h <= hb + 0.1)
    if q.sum(): print("h %.1f n %d lat %.2f-%.2f" % (hb, q.sum(), lat[q].min(), lat[q].max()))
