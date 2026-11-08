"""Pad seat for any arm: the seat of the reference arm in the nearest pose (Springles = Josh's 62 placement, plus Mar Fil arms
whose copied seat passed the audit), turned by the smallest rotation about the shoulder joint that carries the reference's
upper arm onto this arm's, then pushed out along the seat's outward axis until 62 clears the arm."""
import sys, json, math, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from padrule import *
AUD = {r["name"]: r for r in json.load(open("/home/claude/kitbash/kits/pads/arms_audit.json"))}
def updir3(V):
    d = np.linalg.norm(V - J, axis=1); r = d.max(); band = V[(d > 0.35 * r) & (d < 0.65 * r)]
    u = band.mean(0) - J; return u / np.linalg.norm(u)
def rmin(a, b):
    v = np.cross(a, b); s = np.linalg.norm(v); c = a @ b
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]) / s; t = math.atan2(s, c)
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K
def cur_seat(a, S, side): return S @ (sock(a, "Pad R") if side == "R" else conj(sock(a, "Pad L")))
REFS = []
def build_refs(makers=("Springles", "MarFil"), max_tilt=30):
    REFS.clear()
    for a in P:
        if a["type"] != "Arms" or a["maker"] not in makers or a["name"] not in AUD: continue
        if a["maker"] != "Springles" and AUD[a["name"]]["tilt"] > max_tilt: continue
        side, S, V, T = arm_world(a)
        REFS.append(dict(u=updir3(V), seat=cur_seat(a, S, side), name=a["name"], maker=a["maker"], kit=a["kit"]))
def rule_seat(a, exclude_kit=None, push=True):
    side, S, V, T = arm_world(a); u = updir3(V)
    pool = [r for r in REFS if not (exclude_kit and (r["maker"], r["kit"]) == exclude_kit)]
    ref = max(pool, key=lambda r: r["u"] @ u)
    R = np.eye(4); R[:3, :3] = rmin(ref["u"], u)
    W = about_J(R) @ ref["seat"]; moved = 0.0
    if push:
        N = normals(V, T); tree = cKDTree(V)
        out = xf(W @ F62, V62).mean(0) - J; out /= np.linalg.norm(out)
        for k in range(60):
            f, d = inside_frac(xf(W @ F62, V62), V, N, tree)
            if f <= 0.01: break
            W = W.copy(); W[:3, 3] += out * 0.1; moved += 0.1
    return dict(side=side, S=S, seat=W, ref=ref["name"], pose=math.degrees(math.acos(np.clip(ref["u"] @ u, -1, 1))), moved=moved)
