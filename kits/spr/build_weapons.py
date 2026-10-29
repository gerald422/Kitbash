"""Springles hand-held weapons -> sidecars. Hand R fit from the wrist dome of the grip hand:
origin = dome apex pulled back SEAT along the wrist axis (the apex sits on the cup floor, SEAT below the lip),
Y = wrist axis (out of the hand, into the arm), Z = the weapon's up (file +Z) square to Y."""
import sys, json, os, re, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); import stlcache
U = "/mnt/user-data/uploads/new cults/Springles/"
OUT = "/home/claude/kits/out113/stage_spr/Springles/"
K = 1.1; SEAT = 0.55
PIST = ("pistol", "revolver", "hand flamer", "serpenta")
def L16(M): return [round(float(x), 6) for x in np.asarray(M).ravel()]
def frame(apex, a):
    a = np.asarray(a, float); a /= np.linalg.norm(a)
    z = np.array([0, 0, 1.0]) - a[2] * a
    if np.linalg.norm(z) < 0.3: z = np.array([1.0, 0, 0]) - a[0] * a
    z /= np.linalg.norm(z)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = np.cross(a, z), a, z, K * np.asarray(apex) - SEAT * a
    return M
def barrel_axis(rel):
    V, T = stlcache.load(U + rel); P = V - V.mean(0); w, v = np.linalg.eigh(P.T @ P); return v[:, 2]
def pick_grip(rel, ds, nh):
    if len(ds) == 1: return ds[0], None
    if "tabar" in rel:            # both hands on the haft: the lower hand is the right (rear) hand
        s = sorted(ds, key=lambda d: d["apex"][2]); return s[0], s[1]
    b = barrel_axis(nh or rel)
    s = sorted(ds, key=lambda d: -abs(np.dot(d["a"], b)))
    return s[0], s[1]
def category(rel, n):
    b = os.path.basename(rel).lower()
    if any(p in b for p in PIST): return "Pistols"
    if "axe" in b or "tabar" in b: return "Melee" if n == 1 else "Two-Handed Held"
    return "Two-Handed Held" if n >= 2 else None
if __name__ == "__main__":
    from classify import pick, kind
    H = json.load(open("w/hands_final.json"))
    CAT = {"gun": "Two-Handed Held", "heavy": "Two-Handed Held", "tabar2": "Two-Handed Held", "pistol": "Pistols", "axe": "Melee"}
    rep = []
    for rel, h in sorted(H.items()):
        k = kind(rel); g, other = pick(rel, h["domes"])
        if g is None or (CAT[k] == "Two-Handed Held" and other is None):
            rep.append((rel, "SKIP (no hands)")); continue
        F = frame(g["apex"], g["a"])
        d = {"schemaVersion": 1, "part": os.path.basename(rel)[:-4], "category": CAT[k], "scale": K, "sockets": [],
             "fits": {"Hand R": L16(np.linalg.inv(F))},
             "notes": {"Hand R": "Springles wrist dome on the arm's cup (tip %.2f mm into the wrist), the hand's wrist axis along the forearm, weapon up = file +Z" % SEAT}}
        if other is not None:
            d["offHand"] = L16(frame(other["apex"], other["a"]))
            d["pivot"] = [round(float(x), 6) for x in K * np.asarray(g["apex"])]
            d["notes"]["offHand"] = "the other hand's wrist: the gun turns about the right wrist to bring it to the left wrist"
        p = OUT + rel[:-4] + ".sockets.json"; os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(d, open(p, "w"))
        rep.append((rel, CAT[k]))
    from collections import Counter
    print(Counter(r[1] for r in rep)); print([r[0] for r in rep if r[1].startswith("SKIP")])
