"""Runs on the PC (device shell, numpy only). Springles belt bits (pouches, mags, grenades, scanner, tablet, masks...):
they stand up on the plate (Z up), thinnest across X, the flat back on the -X side (the side with more flat area).
Fit = the back face's centre on the belt anchor (Hip R / Hip L / Belt Back: Z out of the belt, Y up), then TIOW rocks
and settles them. Heresy scale x1.1. Writes belt_fits.json.   python3 belt_rule_device.py <folder> <out.json>"""
import os, sys, json, struct, numpy as np
S = 1.1
def load(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), count=n, offset=84)
    return a["v"].astype(float) * S
out = {}
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith(".stl"): continue
    low = f.lower()
    if low.startswith(("belt connector", "melta bomb held", "vexilla")): continue
    V = load(os.path.join(d, f)); e1 = V[:, 1] - V[:, 0]; e2 = V[:, 2] - V[:, 0]; n = np.cross(e1, e2); A = np.linalg.norm(n, axis=1) / 2
    n = n / (2 * A[:, None] + 1e-12); P = V.reshape(-1, 3); lo, hi = P.min(0), P.max(0); ext = hi - lo
    if np.argmin(ext) != 0:
        out[f] = {"skip": "not thinnest across X: %s" % np.round(ext, 1).tolist()}; continue
    fm, fp = A[n[:, 0] < -0.995].sum(), A[n[:, 0] > 0.995].sum()
    back = -1.0 if fm >= fp else 1.0                     # the flatter side is the back
    c = np.array([lo[0] if back < 0 else hi[0], (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2])
    z = np.array([-back, 0, 0]); y = np.array([0, 0, 1.0]); x = np.cross(y, z)
    Pm = np.eye(4); Pm[:3, 0], Pm[:3, 1], Pm[:3, 2], Pm[:3, 3] = x, y, z, c
    Fm = np.linalg.inv(Pm)
    out[f] = {"fit": [round(float(v), 6) for v in Fm.reshape(-1)], "back": "-X" if back < 0 else "+X", "flat": [round(float(fm), 1), round(float(fp), 1)]}
json.dump(out, open(sys.argv[2], "w"), indent=0)
print(sum(1 for v in out.values() if "fit" in v), "fitted,", sum(1 for v in out.values() if "skip" in v), "skipped")
for k, v in out.items():
    if "skip" in v: print("  skip", k, v["skip"])
