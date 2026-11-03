"""Hip plates, buckle and trophy spots on other makers' legs (Turtle Ninja first, Nov 3; Josh: "seat by rule, I
review"; the Mar Fil buckle part over their belt front). Rule, the Assault standing-legs method moved to torso
coordinates (every maker's legs seated under a torso share them): each of the 16 Assault legs gives a starting
pose for the part (plate L, plate R = mirror image, buckle) in torso coordinates; the part's contact points (where
it touches Assault Legs 4A) are seated on the new legs by point-to-plane ICP; best score kept (contact median +
5 x share of the part sunk > 0.3 mm). Trophy R / L: the belt rule 45 deg either side of the way the seated buckle
faces, at the legs' own belt height. Sockets as on the Assault legs (build_tiow.py).
python tn_seat.py OUT_JSON LEGS_REL [LEGS_REL ...]   (library paths without .stl)"""
import sys, os, json, numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hol_common import stl, tf, surf, M16, U, LIB, AM
import belt
OUT, LEGS = sys.argv[1], sys.argv[2:]
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
# contact points: where each part touches Assault Legs 4A
e4 = doc["legs"]["MarFil Assault - Legs 4A"]; LV, LT = stl(U + AM + "Legs(JumpPack)/Legs/MarFil Assault - Legs 4A.stl"); t4 = cKDTree(surf(LV, LT, 300000)[0])
def contacts(V, T, W):
    P, _ = surf(V, T, 60000); return P[t4.query(tf(W, P))[0] < 0.25]
C = {"L": contacts(PV, PT, M16(e4["plates"]["L"]["matrix"])), "R": contacts(PV, PT, M16(e4["plates"]["R"]["matrix"]) @ Sm),
     "B": contacts(BV, BT, M16(e4["buckle_part"]["matrix"]))}
ALL = {"L": surf(PV, PT, 6000)[0], "R": surf(PV, PT, 6000)[0], "B": surf(BV, BT, 6000)[0]}
print("contact points:", {k: len(v) for k, v in C.items()})
def seat(W, S, N, tree, Cp, it=40):
    for _ in range(it):
        X = tf(W, Cp); d, j = tree.query(X); k = d < 1.5
        if k.sum() < 10: break
        X, Q, Nn = X[k], S[j[k]], N[j[k]]; r = ((X - Q) * Nn).sum(1)
        J = np.hstack([np.cross(X, Nn), Nn]); dx = np.linalg.lstsq(J, -r, rcond=None)[0]
        a, t = dx[:3], dx[3:]; th = np.linalg.norm(a)
        R = np.eye(3) if th < 1e-12 else np.cos(th) * np.eye(3) + np.sin(th) * np.array([[0, -a[2] / th, a[1] / th], [a[2] / th, 0, -a[0] / th], [-a[1] / th, a[0] / th, 0]]) + (1 - np.cos(th)) * np.outer(a / th, a / th)
        D = np.eye(4); D[:3, :3] = R; D[:3, 3] = t; W = D @ W
        if th < 1e-6 and np.linalg.norm(t) < 1e-5: break
    return W
def score(W, S, N, tree, Cp, Pall):
    X = tf(W, Cp); d, j = tree.query(X); sd = ((X - S[j]) * N[j]).sum(1)
    Xa = tf(W, Pall); da, ja = tree.query(Xa); pen = (((Xa - S[ja]) * N[ja]).sum(1) < -0.3) & (da < 2)
    return np.median(np.abs(sd)) + 5 * pen.mean(), np.median(np.abs(sd)), pen.mean()
res = {}
for rel in LEGS:
    sc = json.load(open(LIB + rel + ".sockets.json")); M = UP @ FW @ M16(sc["fits"]["Flat Waist"])         # legs file -> torso
    V, T = stl(U + rel + ".stl"); S, N = surf(V, T, 300000); S, N = tf(M, S), N @ M[:3, :3].T; tree = cKDTree(S)
    r = {"why": {}}
    for k in ("L", "R", "B"):
        cands = []
        for W0 in starts[k]:
            W1 = seat(W0, S, N, tree, C[k]); cands.append((score(W1, S, N, tree, C[k], ALL[k]), W1))
        cands.sort(key=lambda c: c[0][0]); (sc_, med, pen), W1 = cands[0]
        spread = max(np.linalg.norm(tf(W1, C[k]) - tf(c[1], C[k]), axis=1).mean() for c in cands[:3])
        r[k] = inv(M) @ W1                                                                                       # part file -> legs file
        r["why"][k] = "contact median %.3f mm, %.1f%% sunk >0.3, next-best seats within %.2f mm" % (med, 100 * pen, spread)
    z = (M @ r["B"] @ ORN)[:3, 2]; az = np.arctan2(z[0], z[1])
    bf = M @ M16([s for s in sc["sockets"] if s["type"] == "Belt Front"][0]["matrix"])
    belt.BELT_Z = bf[2, 3]; belt.AXIS = np.array([0.0, 0.57, belt.BELT_Z])
    belt.DIRS = {"Trophy R": (np.sin(az + np.pi / 4), np.cos(az + np.pi / 4), 0), "Trophy L": (np.sin(az - np.pi / 4), np.cos(az - np.pi / 4), 0)}
    belt.geo.load = lambda p: stl(U + rel + ".stl")
    tr = belt.belt_anchors(rel, M)
    r["sockets"] = {"Plate L": r["L"] @ Pc, "Plate R": r["R"] @ Pc @ A, "Buckle": r["B"] @ ORN, **{k: v for k, v in tr.items()}}
    res[rel] = {"parts": {k: r[k].tolist() for k in "LRB"}, "sockets": {k: v.tolist() for k, v in r["sockets"].items()}, "why": r["why"],
                "buckle_facing_deg": round(float(np.degrees(az)), 1), "belt_z": round(float(belt.BELT_Z), 2)}
    print(rel.split("/")[-1], "| L:", r["why"]["L"], "| R:", r["why"]["R"], "| buckle:", r["why"]["B"], "| faces %.1f deg, belt z %.2f, trophies %s" % (np.degrees(az), belt.BELT_Z, sorted(tr)))
json.dump(res, open(OUT, "w"), indent=0)
