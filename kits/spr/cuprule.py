"""Springles arm wrist: a cup at the end of the forearm (recess ~0.6 deep, inner r ~1.36, lip outer r ~1.87).
Hand socket: origin = centre of the lip's top ring, Y = into the arm, Z = roll rule (torso up+forward)."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real')
import stlcache, fitlib as F
from addon_ns import ns
U = "/mnt/user-data/uploads/new cults/Springles/"
def circle3(P, nn):
    u = np.cross(nn, [0, 0, 1.0]);
    if np.linalg.norm(u) < 0.1: u = np.cross(nn, [1.0, 0, 0])
    u /= np.linalg.norm(u); w = np.cross(nn, u); c0 = P.mean(0); x, y = (P - c0) @ u, (P - c0) @ w
    M = np.c_[2 * x, 2 * y, np.ones_like(x)]; s = np.linalg.lstsq(M, x * x + y * y, rcond=None)[0]
    r = np.sqrt(s[2] + s[0] ** 2 + s[1] ** 2); return c0 + s[0] * u + s[1] * w, r, np.hypot(x - s[0], y - s[1])
def cup(V, T, joint, S=None):
    cen, n, a = ns["_tri_info"](V, T)
    dist = np.linalg.norm(cen - joint, axis=1)
    idx = np.where(dist > 0.55 * dist.max())[0]
    cand = []
    for g, nn, A in ns["_flat_patches"](V, T, cen, n, a, idx, (0.3, 30.0)):
        c = (cen[g] * a[g, None]).sum(0) / A; out = c - joint
        if out @ nn >= 0.5 * np.linalg.norm(out):
            cand.append((float(np.linalg.norm(out)), A, c, nn))
    if not cand: return None
    cand.sort(key=lambda x: -x[0])
    if S is None: S = F.surf(V, T, 250000, 0)
    good = []
    for d_, A, c, nn in cand[:40]:
        ax = nn.copy(); o = c.copy(); ok = True
        for it in range(6):
            L = S - o; h = L @ ax; lat = L - np.outer(h, ax); r = np.linalg.norm(lat, axis=1)
            near = (r < 2.4) & (h > -1.5) & (h < 1.0)
            if near.sum() < 200: ok = False; break
            top = np.quantile(h[near], 0.995)
            ring = near & (h > top - 0.06) & (r > 1.0)
            if ring.sum() < 40: ok = False; break
            P = S[ring]; cc = P.mean(0); u_, s_, vt = np.linalg.svd(P - cc); nz = vt[2] * np.sign(vt[2] @ ax)
            o2, rr, rad = circle3(P, nz)
            ax, o = nz, o2 + nz * ((cc - o2) @ nz)
        if not ok: continue
        L = S - o; h = L @ ax; lat = L - np.outer(h, ax); r = np.linalg.norm(lat, axis=1)
        mid = (r < 0.9) & (h > -1.5) & (h < 0.5)
        if mid.sum() < 30: continue
        depth = -np.quantile(h[mid], 0.98)
        beyond = ((r < 2.0) & (h > 0.15) & (h < 4)).sum()        # nothing in front of the cup
        cupok = 1.55 <= rr <= 1.8 and 0.45 <= depth <= 0.65 and rad.std() / rr < 0.12 and beyond < 30
        if cupok:
            good.append(dict(origin=o, Y=-ax, r_lip=float(rr), spread=float(rad.std() / rr), depth=float(depth), d=d_))
    if good:
        # one cup, found from several of its flats: the farthest from the shoulder
        return max(good, key=lambda g: g["d"])
    return None
def roll_Z(Y_t):
    g = np.array([0, 1.0, 1.0]) / np.sqrt(2)
    z = g - (g @ Y_t) * Y_t
    return z / np.linalg.norm(z)
def hand_socket(rel, a, S_side):
    V, T = stlcache.load(U + rel); V = V * a["scale"]
    Fm = np.array(a["fit"]); j = np.linalg.inv(Fm)[:3, 3]
    c = cup(V, T, j)
    if c is None: return None, None
    W = S_side @ Fm
    Yt = W[:3, :3] @ c["Y"]; Zt = roll_Z(Yt); Z = W[:3, :3].T @ Zt
    X = np.cross(c["Y"], Z); M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = X, c["Y"], Z, c["origin"]
    return M, c
if __name__ == "__main__":
    AF = json.load(open("arm_fits.json"))
    from spr_arms import S_R, S_L
    out = {}; bad = []
    for rel, a in sorted(AF.items()):
        M, c = hand_socket(rel, a, S_R if a["joint"] == "Shoulder R" else S_L)
        if M is None: bad.append(rel); print("NONE", rel, flush=True); continue
        out[rel] = dict(M=M.tolist(), **{k: v for k, v in c.items() if k not in ("origin", "Y")})
        print("%-58s r_lip %.2f sp %.3f depth %.2f" % (rel[-58:], c["r_lip"], c["spread"], c["depth"]), flush=True)
    json.dump(out, open("cups.json", "w"), indent=0)
    print(len(out), "found;", len(bad), "missing")
