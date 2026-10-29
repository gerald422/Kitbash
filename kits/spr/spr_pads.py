"""Pad R/L anchors for the Springles arms: Josh's 62-on-76 anchor carried across relative to the shoulder joint and
the upper arm's swing, then dropped onto the Springles shoulder (the anchor's top point sits on the surface, as on 76)."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real')
import stlcache, geo, fitlib as F
from spr_arms import S_R, S_L, S_H
U = "/mnt/user-data/uploads/new cults/Springles/"; ST = "/home/claude/kits/out113/stage_spr/Springles/"
AM = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
KL = "/home/claude/test/kitlib/All Mar All the time/"
MX = np.diag([-1.0, 1, 1, 1])
def frame(o, x, z):
    x = x / np.linalg.norm(x); z = z - (z @ x) * x; z /= np.linalg.norm(z)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, np.cross(z, x), z, o; return M
def arm_frame(P, d, xout):
    """origin at the shoulder disc, X out of the body along the disc axis, Z from the upper arm up to the shoulder"""
    r = np.linalg.norm(P - d, axis=1); R = r.max()
    mid = P[(r > 0.35 * R) & (r < 0.65 * R)].mean(0)
    return frame(d, xout, d - mid)
def surface_drop(P, M, lat=0.35):
    """height of the surface under the anchor origin along its Z (0 = on the surface)"""
    z = M[:3, 2]; L = P - M[:3, 3]; h = L @ z; l = np.linalg.norm(L - np.outer(h, z), axis=1)
    k = l < lat
    return float(h[k].max()) if k.any() else None
# Josh's example on 76, in torso coordinates
s76 = json.load(open(KL + AM + "Arms/76-Arm-1-R-A.sockets.json"))
f76 = np.array(s76["fits"]["Shoulder R"]).reshape(4, 4)
pad76 = next(np.array(s["matrix"]).reshape(4, 4) for s in s76["sockets"] if s["type"] == "Pad R")
V, T = geo.load(AM + "Arms/76-Arm-1-R-A.stl"); W76 = S_R @ f76
P76 = F.surf(np.asarray(V, float), T, 200000, 0) @ W76[:3, :3].T + W76[:3, 3]
A76 = arm_frame(P76, S_R[:3, 3], np.array([1.0, 0, 0]))
PAD76 = W76 @ pad76
REL = np.linalg.inv(A76) @ PAD76
h76 = surface_drop(P76, PAD76)
def pad_for(rel):
    s = json.load(open(ST + rel[:-4] + ".sockets.json")); side = list(s["fits"])[0][-1]; k = s["scale"]
    Fm = np.array(s["fits"]["Shoulder " + side]).reshape(4, 4)
    W = (S_R if side == "R" else S_L) @ Fm
    V, T = stlcache.load(U + rel); P = F.surf(V * k, T, 200000, 0) @ W[:3, :3].T + W[:3, 3]
    if side == "L": P = P * [-1, 1, 1]                      # work on the mirror image as a right arm
    d = S_H[:3, 3]; xout = S_H[:3, 1]                     # HeresyArms point; the disc faces local -Y (the chest), so out = +Y
    A = arm_frame(P, d, xout)
    M = A @ REL
    h = surface_drop(P, M)
    if h is not None: M[:3, 3] += M[:3, 2] * (h - h76)
    if side == "L": M = MX @ M @ MX
    return side, np.linalg.inv(W) @ M, M, h
if __name__ == "__main__":
    print("76: drop %.3f" % h76, "REL t", REL[:3, 3].round(2))
    for rel in sys.argv[1:]:
        side, Mp, Mt, h = pad_for(rel)
        print(rel.split("/")[-1], side, "torso o", Mt[:3, 3].round(2), "drop", None if h is None else round(h, 2))
# --- pushed out so a pauldron covers the Springles shoulder armour instead of sinking into it
from scipy.spatial import cKDTree
def _pad_inner():
    V, T = geo.load(P62REL); V = np.asarray(V, float)
    S = F.surf(V, T, 40000, 1); N = None
    return S
P62REL = AM + "ShoulderPads/62-ShoulderPad-1.stl"
F62 = np.array(json.load(open(KL + AM + "ShoulderPads/_fits.json"))["Pad R"]["m"]).reshape(4, 4)
_S62 = None
def penetration(P, Pn, tree, pts):
    d, i = tree.query(pts); s = ((pts - P[i]) * Pn[i]).sum(1)
    return s
def push_out(P, Pn, M, d, allow=0.15, frac=0.03):
    """move the anchor along d until no more than `frac` of the pad's points are deeper than `allow` in the arm"""
    global _S62
    if _S62 is None: _S62 = _pad_inner()
    tree = cKDTree(P)
    pad = lambda t: (_S62 @ (M[:3, :3] @ F62[:3, :3]).T) + (M[:3, :3] @ F62[:3, 3] + M[:3, 3] + t * d)
    def bad(t):
        q = pad(t); dd, i = tree.query(q); near = dd < 50
        s = ((q - P[i]) * Pn[i]).sum(1)
        return np.mean(near & (s < -allow))
    lo, hi = 0.0, 0.0
    if bad(0.0) <= frac: return 0.0
    hi = 0.5
    while bad(hi) > frac and hi < 8: hi *= 1.6
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        if bad(mid) > frac: lo = mid
        else: hi = mid
    return hi
def arm_points_normals(V, T, W, n=250000):
    tri = V[T]; a = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(0); i = rng.choice(len(T), n, p=a / a.sum()); u, w = rng.random(n), rng.random(n)
    m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]; t = tri[i]
    P = t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0])
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); fn /= np.linalg.norm(fn, axis=1)[:, None] + 1e-12
    Pn = fn[i]
    return P @ W[:3, :3].T + W[:3, 3], Pn @ W[:3, :3].T
def pad_for2(rel):
    s = json.load(open(ST + rel[:-4] + ".sockets.json")); side = list(s["fits"])[0][-1]; k = s["scale"]
    Fm = np.array(s["fits"]["Shoulder " + side]).reshape(4, 4)
    W = (S_R if side == "R" else S_L) @ Fm
    V, T = stlcache.load(U + rel); V = np.asarray(V, float) * k
    P, Pn = arm_points_normals(V, T, W)
    if side == "L": P = P * [-1, 1, 1]; Pn = Pn * [-1, 1, 1]
    d0 = S_H[:3, 3]; xout = S_H[:3, 1]
    A = arm_frame(P, d0, xout)
    M = A @ REL
    c = (M @ F62)[:3, 3]                                   # roughly the pad's middle
    cen = M[:3, :3] @ (F62[:3, :3] @ _pad_center()) + M[:3, :3] @ F62[:3, 3] + M[:3, 3]
    dvec = cen - d0; dvec /= np.linalg.norm(dvec)
    t = push_out(P, Pn, M, dvec)
    M = M.copy(); M[:3, 3] += t * dvec
    if side == "L": M = MX @ M @ MX
    return side, np.linalg.inv(W) @ M, M, t
_PC = None
def _pad_center():
    global _PC
    if _PC is None:
        V, T = geo.load(P62REL); _PC = np.asarray(V, float).mean(0)
    return _PC
