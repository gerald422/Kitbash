"""Cup check with Mar Fil pad 56 (a near-spherical cup): placed on a seat, its cup centre should sit over the shoulder joint."""
import sys, json, collections, numpy as np, math
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from seatrule import *
P56 = BY["MarFil Bladeguard - Shoulder Pad 1"]; F56 = fit(P56, "Pad R"); V56, T56 = prev(P56)
def _sph(Pp):
    A = np.c_[2 * Pp, np.ones(len(Pp))]; b = (Pp ** 2).sum(1); c, *_ = np.linalg.lstsq(A, b, rcond=None); return c[:3], math.sqrt(c[3] + c[:3] @ c[:3])
C56, R56 = _sph(V56); M56 = V56.mean(0)
def cup(seat):
    W = seat @ F56; c = xf(W, C56[None])[0]; m = xf(W, M56[None])[0]
    return float(np.linalg.norm(c - J)), float(((m - c) / np.linalg.norm(m - c)) @ ((m - J) / np.linalg.norm(m - J)))
if __name__ == "__main__":
    print("56 sphere r %.2f, centre %s, centroid %s" % (R56, np.round(C56, 2), np.round(M56, 2)))
    rows = []
    for a in P:
        if a["type"] != "Arms" or not any(s["t"].startswith("Pad") for s in a.get("sockets", [])): continue
        if fit(a, "Shoulder R") is None and fit(a, "Shoulder L") is None: continue
        side, S, V, T = arm_world(a); d, s = cup(cur_seat(a, S, side))
        rows.append(dict(name=a["name"], fam=a["maker"] + "/" + a["kit"], d=d, s=s))
    json.dump(rows, open("cupcheck.json", "w"))
    b = {r["name"]: r for r in rows}
    for n in ["MarFil Assault - Arm 1A R", "MarFil Intercessor - Arm 1 L", "MarFil Intercessor - Arm 5 L", "BBoosty Medusas Mortals - Arm 2 R", "TN Mk7-8 Assault - Mk7 Power Fist B1", "MarFil Intercessor - Bolter C3 R", "Marta Aggressor - Agrrrr Arm 1 Closed Flamer"]:
        print("%-45s cup-joint %.1f  outward %.2f" % (n, b[n]["d"], b[n]["s"]))
    fam = collections.defaultdict(list)
    for r in rows: fam[r["fam"]].append(r)
    for k, v in sorted(fam.items()):
        d = np.array([r["d"] for r in v]); s = np.array([r["s"] for r in v])
        print("%-32s n=%3d cup-joint med %4.1f p90 %4.1f max %4.1f | outward<0: %d" % (k[:32], len(v), np.median(d), np.percentile(d, 90), d.max(), (s < 0).sum()))
