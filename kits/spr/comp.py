import numpy as np, json, sys
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
def comps(V, T):
    n = len(V); e = np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]
    A = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    k, lab = connected_components(A, directed=False); return k, lab
def largest(V, T):
    k, lab = comps(V, T); lt = lab[T[:, 0]]
    cnt = np.bincount(lt); big = np.argmax(cnt); T2 = T[lt == big]; u, inv = np.unique(T2, return_inverse=True)
    return V[u], inv.reshape(-1, 3)
if __name__ == "__main__":
    for name in ["hand_grip", "hand_fore", "hand_pp"]:
        z = np.load(SCR + name + ".npz"); V, T = z["V"].astype(float), z["T"]
        k, lab = comps(V, T); lt = lab[T[:, 0]]; cnt = np.bincount(lt)
        print(name, "components", k, "largest tris", sorted(cnt)[-3:])
        V2, T2 = largest(V, T); np.savez(SCR + name + "_big.npz", V=V2.astype(np.float32), T=T2.astype(np.int32))
        print("   bbox", V2.min(0).round(2), V2.max(0).round(2))
