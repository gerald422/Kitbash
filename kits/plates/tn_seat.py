"""Hip plates, buckle and trophy spots on other makers' legs (Turtle Ninja first, Nov 3; Josh: "seat by rule, I
review"; the Mar Fil buckle part over their belt front). Rule, the Assault standing-legs method moved to torso
coordinates (every maker's legs seated under a torso share them): each of the 16 Assault legs gives a starting
pose for the part (plate L, plate R = mirror image, buckle) in torso coordinates; the part's contact points (where
it touches Assault Legs 4A) are seated on the new legs by point-to-plane ICP; best score kept (contact median +
5 x share of the part sunk > 0.3 mm). Trophy R / L: the belt rule 45 deg either side of the way the seated buckle
faces, at the legs' own belt height. Then each plate is re-seated with its top edge on the belt (Josh, as on every
Assault legs), a 26 deg roll (outer face looking up; Josh: R was too high, L too low) and the top edge
nearly level like the Assault plates (tilt -1.3 / -1.8 deg). Sockets as on the Assault legs (build_tiow.py).
python tn_seat.py OUT_JSON [--stl ROOT] [--jobs N] [--list LEGS_JSON] [LEGS_REL ...]   (library paths without .stl;
resumes: legs already in OUT_JSON are skipped)"""
import sys, os, json, time, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hol_common import stl, tf, surf, M16, U, LIB, AM
import belt
ARGS = sys.argv[1:]; OUT = ARGS.pop(0)
def opt(k, d=None):
    if k in ARGS: i = ARGS.index(k); v = ARGS[i + 1]; del ARGS[i:i + 2]; return v
    return d
STL = opt("--stl", U); JOBS = int(opt("--jobs", "1")); LST = opt("--list")
LEGS = json.load(open(LST)) if LST else ARGS
inv = np.linalg.inv; A = np.diag([-1.0, 1, 1, 1])
doc = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "marfil_assault_plates.json")))
Pc, Sm = M16(doc["plate_frame"]["matrix"]), M16(doc["plate_self_mirror"]["matrix"])
ORN = M16(doc["buckle_part"]["sockets"]["Buckle Ornament"]["matrix"])
T1 = json.load(open(LIB + AM + "Chests/MarFil Assault - Torso 1.sockets.json"))
S_WAIST = M16([s for s in T1["sockets"] if s["type"] == "Waist"][0]["matrix"])
TT = json.load(open(LIB + "Turtle Ninja - Heresy/Mk7-8 Builder/Mk7-8/Chests/TN Mk7-8 - Mk8 Torso A1.sockets.json"))
UP, FW = M16(TT["upright"]), M16([s for s in TT["sockets"] if s["type"] == "Flat Waist"][0]["matrix"])
PV, PT = stl(U + AM + "Hip Plates/MarFil Assault - Hip Plate L.stl"); BV, BT = stl(U + AM + "Buckles/MarFil Assault - Buckle.stl")
# starting poses (part file -> torso coordinates) from the 16 Assault legs
starts = {"L": [], "R": [], "B": []}
for name, e in doc["legs"].items():
    sc = json.load(open(LIB + AM + e["folder"] + "/" + name + ".sockets.json")); M = S_WAIST @ M16(sc["fits"]["Waist"])
    starts["L"].append(M @ M16(e["plates"]["L"]["matrix"])); starts["R"].append(M @ M16(e["plates"]["R"]["matrix"]) @ Sm)
    starts["B"].append(M @ M16(e["buckle_part"]["matrix"]))
def dedupe(Ws, P, tol=0.5):        # drop starting poses within tol mm (mean over the part's points) of one kept
    keep = []
    for W in Ws:
        if all(np.linalg.norm(tf(W, P) - tf(K, P), axis=1).mean() > tol for K in keep): keep.append(W)
    return keep
_pp = PV[::max(1, len(PV) // 400)]; _bp = BV[::max(1, len(BV) // 400)]
starts = {"L": dedupe(starts["L"], _pp), "R": dedupe(starts["R"], _pp), "B": dedupe(starts["B"], _bp)}
print("starting poses after dedupe:", {k: len(v) for k, v in starts.items()})
# contact points: where each part touches Assault Legs 4A
e4 = doc["legs"]["MarFil Assault - Legs 4A"]; LV, LT = stl(U + AM + "Legs(JumpPack)/Legs/MarFil Assault - Legs 4A.stl"); t4 = cKDTree(surf(LV, LT, 300000)[0])
def contacts(V, T, W):
    P, _ = surf(V, T, 60000); return P[t4.query(tf(W, P))[0] < 0.25]
C = {"L": contacts(PV, PT, M16(e4["plates"]["L"]["matrix"])), "R": contacts(PV, PT, M16(e4["plates"]["R"]["matrix"]) @ Sm),
     "B": contacts(BV, BT, M16(e4["buckle_part"]["matrix"]))}
ALL = {"L": surf(PV, PT, 6000)[0], "R": surf(PV, PT, 6000)[0], "B": surf(BV, BT, 6000)[0]}
rng = np.random.default_rng(0); C = {k: v[rng.choice(len(v), min(len(v), 3000), replace=False)] for k, v in C.items()}
print("contact points:", {k: len(v) for k, v in C.items()})
# level the pair (Josh, Nov 3: "the roll is slightly out with hip r too high and hip l too low"): both plates to the
# pair's mean height and the same roll - how far the plate's outer face looks up (its flare) - 26 deg, the middle of
# the Assault plates' medians (R 29.8, L 22.3); still seated on the hips by their contact points
c0 = (PV.min(0) + PV.max(0)) / 2; PS, PN = surf(PV, PT, 20000)
def edge(W, side):    # plate centre, the mean normal of its outer face, and its top edge's direction (front to back)
    c = tf(W, c0[None])[0]; N = PN @ W[:3, :3].T; n = N[N @ np.array([1.0 if side == "R" else -1.0, 0, 0]) > 0.3].mean(0)
    P = tf(W, PV); top = P[P[:, 2] > np.percentile(P[:, 2], 85)]; e = np.linalg.svd(top - top.mean(0))[2][0]
    e = e if e[1] >= 0 else -e
    return c, n / np.linalg.norm(n), e
ROLL = 26.0
TILT = {"R": -1.3, "L": -1.8}       # the Assault plates' top edge: nearly level (median tilt per side, deg)
# the top edge that sits against the belt (Josh: "shouldn't the top of the plate always be touching the belt?"; on
# Assault 4A it does, 0.01 mm): plate points in the top 0.4 mm that touch 4A's belt, per side
TOPE = {}
for k, W4 in (("L", M16(e4["plates"]["L"]["matrix"])), ("R", M16(e4["plates"]["R"]["matrix"]) @ Sm)):
    X = tf(W4, PS); m = (X[:, 2] > X[:, 2].max() - 0.4) & (t4.query(X)[0] < 0.3); TOPE[k] = PS[m]
print("top-edge points touching the belt on 4A:", {k: len(v) for k, v in TOPE.items()})
def seat(W, S, N, tree, Cp, it=30, top=None, side=None, w=None):
    """point-to-plane ICP of the contact points Cp onto the surface (S, N); rotations about the contact centre and
    damped steps (<= 0.5 mm, ~3 deg) so far starts don't swing off; optional soft targets: top edge on the belt
    (`top` points), roll ROLL and top-edge tilt TILT[side]."""
    for _ in range(it):
        X = tf(W, Cp); d, j = tree.query(X); k = d < 1.5
        if k.sum() < 10: break
        X, Q, Nn = X[k], S[j[k]], N[j[k]]; r = ((X - Q) * Nn).sum(1); m = X.mean(0)
        J = np.hstack([np.cross(X - m, Nn), Nn])
        if top is not None:                    # the top edge onto the belt, and the roll (outer face elevation)
            Xt = tf(W, top); dt, jt = tree.query(Xt); kt = dt < 1.5; Xt, Qt, Nt = Xt[kt], S[jt[kt]], N[jt[kt]]; wt = 3.0
            c, n, e = edge(W, side); w = w or 4 * np.sqrt(len(r))
            J = np.vstack([J, wt * np.hstack([np.cross(Xt - m, Nt), Nt]), w * 10 * np.array([n[1], -n[0], 0, 0, 0, 0]),
                           w * 10 * np.array([e[1], -e[0], 0, 0, 0, 0])])
            r = np.r_[r, wt * ((Xt - Qt) * Nt).sum(1), w * 10 * (n[2] - np.sin(np.radians(ROLL))), w * 10 * (e[2] - np.sin(np.radians(TILT[side])))]
        dx = np.linalg.lstsq(J, -r, rcond=None)[0]
        a, t = dx[:3], dx[3:]; th = np.linalg.norm(a)
        if th > 0.05: a, th = a * 0.05 / th, 0.05
        if np.linalg.norm(t) > 0.5: t = t * 0.5 / np.linalg.norm(t)
        R = np.eye(3) if th < 1e-12 else np.cos(th) * np.eye(3) + np.sin(th) * np.array([[0, -a[2] / th, a[1] / th], [a[2] / th, 0, -a[0] / th], [-a[1] / th, a[0] / th, 0]]) + (1 - np.cos(th)) * np.outer(a / th, a / th)
        D = np.eye(4); D[:3, :3] = R; D[:3, 3] = m - R @ m + t; W = D @ W
        if th < 1e-6 and np.linalg.norm(t) < 1e-5: break
    return W


def score(W, S, N, tree, Cp, Pall):
    X = tf(W, Cp); d, j = tree.query(X); sd = ((X - S[j]) * N[j]).sum(1)
    Xa = tf(W, Pall); da, ja = tree.query(Xa); pen = (((Xa - S[ja]) * N[ja]).sum(1) < -0.3) & (da < 2)
    return np.median(np.abs(sd)) + 5 * pen.mean(), np.median(np.abs(sd)), pen.mean()
def seat_one(rel):
    sc = json.load(open(LIB + rel + ".sockets.json")); M = UP @ FW @ M16(sc["fits"]["Flat Waist"])         # legs file -> torso
    V, T = stl(STL + rel + ".stl"); S, N = surf(V, T, 150000); S, N = tf(M, S), N @ M[:3, :3].T; tree = cKDTree(S)
    r = {"why": {}}
    for k in ("L", "R"):                       # every start through the whole rule; the best finished seat wins
        cands = []
        for W0 in starts[k]:
            W1 = seat(W0, S, N, tree, C[k]); W2 = seat(W1, S, N, tree, C[k], top=TOPE[k], side=k)
            sc_, med, pen = score(W2, S, N, tree, C[k], ALL[k]); g = tree.query(tf(W2, TOPE[k]))[0]
            c, n, e = edge(W2, k); roll = np.degrees(np.arcsin(np.clip(n[2], -1, 1)))
            ok = 3.5 < abs(c[0]) < 8.5 and 19.0 < c[2] < 24.0 and (c[0] > 0) == (k == "R")
            cands.append((med + 5 * pen + np.median(g) + abs(roll - ROLL) / 10 + (0 if ok else 100), W2, med, pen, np.median(g), g.min(), roll, c))
        cands.sort(key=lambda c: c[0]); best = cands[0]
        spread = max(np.linalg.norm(tf(best[1], C[k]) - tf(c[1], C[k]), axis=1).mean() for c in cands[:3])
        r[k] = inv(M) @ best[1]
        r["why"][k] = ("top on the belt (median %.2f, min %.2f mm), roll %+.1f deg, centre z %.2f; contact median %.3f mm, %.1f%% sunk >0.3; "
                       "next-best seats within %.2f mm%s") % (best[4], best[5], best[6], best[7][2], best[2], 100 * best[3], spread, "" if best[0] < 100 else "; OUT OF THE HIP AREA - CHECK")
    cands = []
    for W0 in starts["B"]:
        W1 = seat(W0, S, N, tree, C["B"]); cands.append((score(W1, S, N, tree, C["B"], ALL["B"]), W1))
    cands.sort(key=lambda c: c[0][0]); (sc_, med, pen), W1 = cands[0]
    r["B"] = inv(M) @ W1; r["why"]["B"] = "contact median %.3f mm, %.1f%% sunk >0.3" % (med, 100 * pen)
    z = (M @ r["B"] @ ORN)[:3, 2]; az = np.arctan2(z[0], z[1])
    bf = M @ M16([s for s in sc["sockets"] if s["type"] == "Belt Front"][0]["matrix"])
    belt.BELT_Z = bf[2, 3]; belt.AXIS = np.array([0.0, 0.57, belt.BELT_Z])
    belt.DIRS = {"Trophy R": (np.sin(az + np.pi / 4), np.cos(az + np.pi / 4), 0), "Trophy L": (np.sin(az - np.pi / 4), np.cos(az - np.pi / 4), 0)}
    belt.geo.load = lambda p: stl(STL + rel + ".stl")
    tr = belt.belt_anchors(rel, M)
    r["sockets"] = {"Plate L": r["L"] @ Pc, "Plate R": r["R"] @ Pc @ A, "Buckle": r["B"] @ ORN, **{k: v for k, v in tr.items()}}
    return rel, {"parts": {k: r[k].tolist() for k in "LRB"}, "sockets": {k: v.tolist() for k, v in r["sockets"].items()}, "why": r["why"],
                "buckle_facing_deg": round(float(np.degrees(az)), 1), "belt_z": round(float(belt.BELT_Z), 2)}
if __name__ == "__main__":
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    todo = [r for r in LEGS if r not in res]; t0 = time.time()
    print("legs to seat:", len(todo), "jobs", JOBS, flush=True)
    if JOBS > 1:
        import multiprocessing as mp
        it = mp.get_context("fork").Pool(JOBS).imap_unordered(seat_one, todo)
    else:
        it = map(seat_one, todo)
    for n, (rel, r) in enumerate(it, 1):
        res[rel] = r
        if n % 10 == 0 or n == len(todo):
            json.dump(res, open(OUT, "w"), indent=0); print("%d/%d legs, %.0f s" % (n, len(todo), time.time() - t0), flush=True)
    json.dump(res, open(OUT, "w"), indent=0)
