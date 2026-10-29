"""Springles hand-held weapons: find the hands (versus the 'no hands' version) and each hand's wrist dome."""
import sys, json, os, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real')
import stlcache, fitlib as F
from scipy.spatial import cKDTree
from domes import domes, U
from comp import comps
def align(V1, T1, V0, T0):
    S0 = F.surf(V0, T0, 120000, 1); S1 = F.surf(V1, T1, 12000, 2); tree = cKDTree(S0)
    best = None
    c1, c0 = S1.mean(0), S0.mean(0)
    for t0 in [c0 - c1] + [c0 - c1 + np.array(d) for d in ((2, 0, 0), (-2, 0, 0), (0, 2, 0), (0, -2, 0))]:
        R, t, d = F.icp(S1, tree, np.eye(3), t0, 30, 0.6)
        m = np.median(np.sort(d)[:len(d) // 2])
        if best is None or m < best[0]: best = (m, R, t)
    return best
def hand_mesh(V1, T1, V0, T0):
    m, R, t = align(V1, T1, V0, T0)
    S0 = F.surf(V0, T0, 400000, 3); tree = cKDTree(S0)
    c = V1[T1].mean(1) @ R.T + t
    d, _ = tree.query(c); k = d > 0.2
    T2 = T1[k]
    if not len(T2): return m, None, None
    u, inv = np.unique(T2, return_inverse=True); V2 = V1[u]; T2 = inv.reshape(-1, 3)
    n, lab = comps(V2, T2); lt = lab[T2[:, 0]]; cnt = np.bincount(lt)
    keep = np.isin(lt, np.where(cnt > 300)[0])
    T3 = T2[keep]; u, inv = np.unique(T3, return_inverse=True)
    return m, V2[u], inv.reshape(-1, 3)
def find(rel, nh):
    V1, T1 = stlcache.load(U + rel)
    S1 = F.surf(V1, T1, 300000, 0)
    info = {}
    if nh:
        V0, T0 = stlcache.load(U + nh)
        m, Vh, Th = hand_mesh(V1, T1, V0, T0); info["align"] = float(m)
        if Vh is None: return info, []
        ds = domes(Vh, Th, S1)
    else:
        ds = domes(V1, T1, S1)
    return info, ds
if __name__ == "__main__":
    sel = json.load(open("w/sel_raw.json"))
    out = {}
    names = sys.argv[1:] or sorted(sel)
    for rel in names:
        if "heavy weapons/" in rel or "assault cannon" in rel: pass
        info, ds = find(rel, sel[rel])
        out[rel] = dict(info, domes=[{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in d.items()} for d in ds])
        print("%-62s align %s  domes %d  %s" % (rel[-62:], "%.3f" % info["align"] if "align" in info else "-", len(ds),
              " | ".join("a %s R %.2f" % (np.round(d["a"], 2), d["R"]) for d in ds)), flush=True)
    json.dump(out, open("w/hands_%s.json" % (os.getpid() if sys.argv[1:] else "all"), "w"), indent=0)
