import sys; sys.path.insert(0, '/home/claude/kits')
import geo, numpy as np, os, json
from scipy.spatial import cKDTree
from fist import side, rel_of, Hof
def build():
    H = Hof(rel_of('211-BoltPistol-R'))     # Josh's/shared frame; the -1 fists sit in the same place
    def pts(stem, n=300000):
        V, T = geo.load(rel_of(stem)); S = geo.surf(V, T, n); return (S - H[:3, 3]) @ H[:3, :3]
    A = pts('193-PowerHammer-A-1-R')
    A = A[(A[:, 1] > -6.5) & (A[:, 1] < 0.4) & (np.linalg.norm(A[:, [0, 2]], axis=1) < 5)]
    keep = np.ones(len(A), bool)
    for s in ('211-BoltPistol-R', '178-CombatKnife-1-R', '184-PowerAxe-A-1-R'):
        keep &= cKDTree(pts(s)).query(A)[0] < 0.08
    F = A[keep]
    # thin to ~2500 evenly
    key = np.unique(np.floor(F / 0.12).astype(int), axis=0, return_index=True)[1]
    F = F[key]
    print('reference fist points', len(F), 'extent', F.min(0).round(2), F.max(0).round(2))
    np.save('/home/claude/kits/fistref.npy', F)
    return F
if __name__ == '__main__':
    F = build()
    import qr
    # render the reference fist as points? quick: save as ply-ish via small spheres is heavy; just print stats
