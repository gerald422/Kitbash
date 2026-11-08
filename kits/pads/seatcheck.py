"""Plausibility of a pad seat, from 62's own shape: its opening (concave side) should hang along the upper arm, and its
front edge should point the torso's way. Angles in degrees."""
import sys, math, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from seatrule import *
def _sphere(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); c, *_ = np.linalg.lstsq(A, b, rcond=None); return c[:3]
L62 = xf(F62, V62)                      # 62 in its socket frame
_m = L62.mean(0); _c = _sphere(L62); O_LOC = (_c - _m) / np.linalg.norm(_c - _m)
_X = L62 - _m; _X -= np.outer(_X @ O_LOC, O_LOC); _w, _U = np.linalg.eigh(_X.T @ _X); LONG_LOC = _U[:, -1]
def desc(seat, u):
    R = rot(seat); o = R @ O_LOC; lg = R @ LONG_LOC
    hang = math.degrees(math.acos(np.clip(o @ u, -1, 1)))
    f = np.array([0, 1.0, 0]); f = f - (f @ u) * u; f /= np.linalg.norm(f)          # torso front, square to the arm
    l2 = lg - (lg @ u) * u; l2 /= np.linalg.norm(l2)
    roll = math.degrees(math.acos(abs(np.clip(l2 @ f, -1, 1))))
    return hang, roll
if __name__ == "__main__":
    import collections, json
    rows = []
    for a in P:
        if a["type"] != "Arms" or not any(s["t"].startswith("Pad") for s in a.get("sockets", [])): continue
        if fit(a, "Shoulder R") is None and fit(a, "Shoulder L") is None: continue
        side, S, V, T = arm_world(a); u = updir3(V); h, r = desc(cur_seat(a, S, side), u)
        rows.append(dict(name=a["name"], maker=a["maker"], kit=a["kit"], hang=h, roll=r))
    json.dump(rows, open("seatcheck.json", "w"))
    b = {r["name"]: r for r in rows}
    for n in ["MarFil Assault - Arm 1A R", "MarFil Intercessor - Arm 1 L", "MarFil Intercessor - Bolter C3 R", "MarFil Intercessor - Bolter A Grenade 3 L", "TN Mk7-8 Assault - Mk7 Power Fist B1", "MarFil Assault - Arm 7B R", "MarFil Intercessor - Plasma Incinerator 4B R"]:
        print("%-45s hang %5.1f roll %5.1f" % (n, b[n]["hang"], b[n]["roll"]))
    fam = collections.defaultdict(list)
    for r in rows: fam[(r["maker"], r["kit"])].append(r)
    print("%-30s %4s %s" % ("family", "n", "hang med / p90 / n>60 | roll med / n>45"))
    for k, v in sorted(fam.items()):
        h = np.array([r["hang"] for r in v]); ro = np.array([r["roll"] for r in v])
        print("%-30s %4d %5.1f %5.1f %3d | %5.1f %3d" % (k[0] + "/" + k[1][:20], len(v), np.median(h), np.percentile(h, 90), (h > 60).sum(), np.median(ro), (ro > 45).sum()))
