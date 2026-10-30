"""Two-armed pieces: match the shoulder joints of a piece known to sit right (Bladeguard Great Sword A, both
inner faces on the sockets within 0.1 mm) onto each piece; the inverse is the move that seats it.
python3 two_icp.py BUILDER [names...] [--all] [--json out.json]"""
import json, struct, sys, numpy as np
from scipy.spatial import cKDTree
B = sys.argv[1]
d = json.load(open(B + "/index.json")); P = {p["name"]: p for p in d["parts"]}
M4 = lambda a: np.array(a, float).reshape(4, 4)
S = {s["t"]: M4(s["m"]) for s in P["MarFil Assault - Torso 3"]["sockets"]}
sR, sL = S["Shoulder R"][:3, 3], S["Shoulder L"][:3, 3]
def surf(p, n=60000, seed=0):
    b = open(B + "/" + p["prev"], "rb").read(); nv, nt = struct.unpack_from("<II", b, 4)
    V = np.frombuffer(b, np.float32, nv * 3, 12).reshape(-1, 3).astype(float); T = np.frombuffer(b, np.uint32, nt * 3, 12 + nv * 12).reshape(-1, 3)
    W = S["Shoulder R"] @ M4(p["fits"]["Shoulder R"]); V = V @ W[:3, :3].T + W[:3, 3]
    A, Bv, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; ar = np.linalg.norm(np.cross(Bv - A, C - A), axis=1)
    rng = np.random.default_rng(seed); i = rng.choice(len(T), n, p=ar / ar.sum()); u, v = rng.random(n), rng.random(n); f = u + v > 1; u[f], v[f] = 1 - u[f], 1 - v[f]
    return A[i] + u[:, None] * (Bv[i] - A[i]) + v[:, None] * (C[i] - A[i])
def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b
    if np.linalg.norm(v) < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1 / (1 + c))
def kabsch(a, b):
    ma, mb = a.mean(0), b.mean(0); H = (a - ma).T @ (b - mb); U, _, Vt = np.linalg.svd(H); D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    R = Vt.T @ D @ U.T; return R, mb - R @ ma
ref = surf(P["MarFil Bladeguard - Great Sword A"])
reg = np.vstack([ref[np.linalg.norm(ref - sR, axis=1) < 4.5], ref[np.linalg.norm(ref - sL, axis=1) < 4.5]])
reg = reg[::max(1, len(reg) // 2000)]
nR = int((np.linalg.norm(reg - sR, axis=1) < 4.6).sum())
def icp(tree, tgt, R, t, it=60):
    for _ in range(it):
        Q = reg @ R.T + t; dd, ii = tree.query(Q); k = dd <= np.quantile(dd, 0.85); R, t = kabsch(reg[k], tgt[ii[k]])
    dd, _ = tree.query(reg @ R.T + t); return R, t, float(np.median(dd)), float(np.quantile(dd, 0.9))
names = [a for a in sys.argv[2:] if not a.startswith("--") and not a.endswith(".json")]
if "--all" in sys.argv:
    names = sorted(p["name"] for p in d["parts"] if p["type"] in ("Two-Handed Guns", "Two-Handed Melee", "Heavy Weapons") and p["maker"] == "MarFil" and p.get("prev"))
    a = sys.argv.index("--all"); names = names[int(sys.argv[a + 1]):int(sys.argv[a + 2])]
res = {}
for n in names:
    p = P[n]; tgt = surf(p, 30000); tree = cKDTree(tgt); best = None
    for dz in (0, -3, 3):
        for dy in (0, 3):
            for ax in (0,):
                c, s_ = np.cos(np.radians(ax)), np.sin(np.radians(ax)); R0 = np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]])
                mid = (sR + sL) / 2; t0 = mid - R0 @ mid + [0, dy, dz]
                R, t, m, q9 = icp(tree, tgt, R0, t0, 30)
                if best is None or m < best[2]: best = (R, t, m, q9)
    R, t, m, q9 = best
    # where the piece's shoulder joints are: the reference joints carried by the match. The joint is round about
    # the shoulder axis, so the match can't tell the arms' swing about it: keep the piece's own (no twist), and
    # only line the two joints up with the two sockets.
    cR, cL = R @ sR + t, R @ sL + t
    dd, _ = tree.query(reg @ R.T + t); mR, mL = float(np.median(dd[:nR])), float(np.median(dd[nR:]))
    Rs = rot_between(cL - cR, sL - sR); mid_c, mid_s = (cR + cL) / 2, (sR + sL) / 2
    C = np.eye(4); C[:3, :3] = Rs; C[:3, 3] = mid_s - Rs @ mid_c
    ang = np.degrees(np.arccos(np.clip((np.trace(Rs) - 1) / 2, -1, 1))); mv = np.linalg.norm(mid_s - mid_c)
    Wp = S["Shoulder R"] @ M4(p["fits"]["Shoulder R"]); Fn = np.linalg.inv(S["Shoulder R"]) @ C @ Wp
    res[p["id"]] = {"name": n, "path": p["path"], "fit": Fn.ravel().tolist(), "med": m, "q90": q9, "rot": float(ang), "move": float(mv)}
    res[p["id"]].update({"medR": mR, "medL": mL, "offR": (cR - sR).round(2).tolist(), "offL": (cL - sL).round(2).tolist()})
    print("%-48s R %.2f L %.2f match %.3f (90%% %.3f)  R off %s  L off %s  move %.2f mm  turn %.1f" % (n[:48], mR, mL, m, q9, (cR - sR).round(1), (cL - sL).round(1), mv, ang))
if "--json" in sys.argv:
    o = sys.argv[sys.argv.index("--json") + 1]
    try: old = json.load(open(o))
    except Exception: old = {}
    old.update(res); res = old
    json.dump(res, open(sys.argv[sys.argv.index("--json") + 1], "w"))
