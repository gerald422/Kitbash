"""Springles hand wrists: a shallow dome (sphere R ~2.2 file units, base r ~1.4, height ~0.5) on the end of the hand.
domes(V, T) -> [dict(apex, a (out of the hand), R, cover, n)]"""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real'); import stlcache, fitlib as F
from addon_ns import ns
U = "/mnt/user-data/uploads/new cults/Springles/"
R_DOME = 2.42
def refine(V, N, c, rr, a):
    """centre of the dome with its radius fixed at Springles' R_DOME (file units); a = axis from the cap's points"""
    rr = R_DOME
    for it in range(10):
        d = np.linalg.norm(V - c, axis=1); u = (V - c) / d[:, None]
        on = (np.abs(d - rr) < 0.07) & ((u * N).sum(1) > 0.85) & (u @ a > np.cos(np.radians(36)))
        if on.sum() < 15: return None
        P = V[on]
        for gn in range(5):        # Gauss-Newton on the centre, radius fixed
            D = P - c; dn = np.linalg.norm(D, axis=1); r_ = dn - rr; J = -D / dn[:, None]
            c = c - np.linalg.lstsq(J, r_, rcond=None)[0]
        u = (P - c) / np.linalg.norm(P - c, axis=1)[:, None]
        a2 = u.mean(0); a = a2 / np.linalg.norm(a2)
    d = np.linalg.norm(V - c, axis=1); u = (V - c) / d[:, None]
    on = (np.abs(d - rr) < 0.05) & ((u * N).sum(1) > 0.9) & (u @ a > np.cos(np.radians(36)))
    return c, rr, a, on
def sphere_votes(V, N, r, cell=0.1, minvotes=20, top=40):
    """every vertex votes for the point one radius inside along its normal; the piles are sphere centres"""
    C = V - r * N; out = []
    for shift in (0.0, 0.5):
        key = np.floor(C / cell + shift).astype(np.int64)
        uk, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
        inv = inv.reshape(-1)
        for k in np.argsort(-cnt)[:top]:
            if cnt[k] < minvotes: break
            c = C[inv == k].mean(0)
            if all(np.linalg.norm(c - o[0]) > 0.5 for o in out): out.append((c, r, int(cnt[k])))
    return out
def domes(V, T, S=None):
    V = np.asarray(V, float); N = ns["_vertex_normals"](V, T)
    if S is None: S = F.surf(V, T, 300000, 0)
    out = []
    for r in (2.0, 2.2, 2.4):
        for c, rr, on in sphere_votes(V, N, r):
            if not (1.7 < rr < 3.2): continue
            d = np.linalg.norm(V - c, axis=1); u = (V - c) / d[:, None]
            k = (np.abs(d - rr) < 0.05) & ((u * N).sum(1) > 0.9)
            if k.sum() < 15: continue
            a = u[k].mean(0); a /= np.linalg.norm(a)
            got = refine(V, N, c, rr, a)
            if got is None: continue
            c, rr, a, onm = got
            apex = c + rr * a
            L = S - apex; h = L @ a; lat = np.linalg.norm(L - np.outer(h, a), axis=1)
            front = int(((h > 0.08) & (lat < 2.0)).sum())
            # ring of the dome surface at 15-33 deg from the axis all round
            Lc = S - c; dc = np.linalg.norm(Lc, axis=1); uc = Lc / dc[:, None]
            ang = np.degrees(np.arccos(np.clip(uc @ a, -1, 1)))
            ring = (np.abs(dc - rr) < 0.05) & (ang > 12) & (ang < 30)
            X0, _y, Z0 = ns["_plane_basis"](a).T
            W = Lc[ring]; az = np.degrees(np.arctan2(W @ Z0, W @ X0))
            cover = len(np.unique(np.floor(az / 15))) / 24.0
            if any(np.linalg.norm(apex - o["apex"]) < 1.0 for o in out): continue
            out.append(dict(apex=apex, a=a, c=c, R=rr, cover=cover, front=front, n=int(onm.sum())))
    return [o for o in out if o["cover"] >= 0.85 and o["front"] < 8000 and o["n"] >= 150]
if __name__ == "__main__":
    for f in sys.argv[1:]:
        V, T = stlcache.load(U + f)
        ds = domes(V, T)
        print(f[-50:], len(ds))
        for o in ds: print("    apex %s a %s R %.2f cover %.2f front %d n %d" % (o["apex"].round(2), o["a"].round(2), o["R"], o["cover"], o["front"], o["n"]))
