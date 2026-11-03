"""Library holsters, pouches and grenades onto the hip plate (Josh, Nov 3: plates only, grenades too).
Rule, from Josh's AM-V2 pistol sheath on Plate Hang L (its top 2.1 mm above the hang point, back on the plate):
orientation = the part's belt fit (back on the anchor, outer face +Z, top +Y; the same frame as Plate Hang),
turned 180 deg about Y where FLIP says (grip forward); centred on the hang point across, top at y = 2.1,
then moved along Z until its deepest point is 0.2 mm under the plate's outer face (height map), so it prints as one piece.
python hol_fit.py PARTS_JSON OUT_JSON [FLIP names,comma separated] [ORIENT_JSON]"""
import sys, json, numpy as np; sys.path.insert(0, __file__.rsplit("/", 1)[0]); from hol_common import *
parts = json.load(open(sys.argv[1])); OUT = sys.argv[2]
FLIP = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else set()
ORI = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}        # name -> 3x3 rotation for parts with no belt fit
TOP, SINK = 2.1, 0.2
S, N = surf(PVs, PT, 400000)
CELL = 0.05; X0, Y0 = S[:, 0].min(), S[:, 1].min()                # height map of the plate's outer face (+Z of Plate Hang)
HM = np.full((int((S[:, 0].max() - X0) / CELL) + 1, int((S[:, 1].max() - Y0) / CELL) + 1), np.nan)
ii = ((S[:, 0] - X0) / CELL).astype(int); jj = ((S[:, 1] - Y0) / CELL).astype(int)
for a_, b_, z_ in zip(ii, jj, S[:, 2]):
    if not (HM[a_, b_] >= z_): HM[a_, b_] = z_
res = {}
for rel in parts:
    name = rel.split("\\")[-1][:-4]; p = rel.replace("\\", "/")
    d = json.load(open(LIB + p[:-4] + ".sockets.json"))
    R = np.array(ORI[name]) if name in ORI else M16(d["fits"]["Hip L"])[:3, :3] if "Hip L" in d.get("fits", {}) else np.eye(3)
    if name in FLIP: R = np.diag([-1.0, 1, -1]) @ R          # 180 deg about the socket's Y: grip the other way
    V, T = stl(U + p); X = V @ R.T
    t = np.array([-(X[:, 0].min() + X[:, 0].max()) / 2, TOP - X[:, 1].max(), 0.0])
    Xs, _ = surf(V, T, 30000); Xs = Xs @ R.T + t
    i = np.floor((Xs[:, 0] - X0) / CELL).astype(int); j = np.floor((Xs[:, 1] - Y0) / CELL).astype(int)
    ok = (i >= 0) & (i < HM.shape[0]) & (j >= 0) & (j < HM.shape[1]); zp = np.full(len(Xs), np.nan); zp[ok] = HM[i[ok], j[ok]]
    g = Xs[:, 2] - zp; g = g[np.isfinite(g)]                   # height of each part point above the plate's outer face
    hi = -SINK - g.min()                                        # shift so the deepest point is SINK into the plate
    t[2] = hi; cover = len(g) / len(Xs); F = np.eye(4); F[:3, :3] = R; F[:3, 3] = t
    res[rel] = {"fit": F.reshape(-1).round(6).tolist(), "deep": SINK, "over_plate": round(cover, 2), "size": (X.max(0) - X.min(0)).round(2).tolist(), "flip": name in FLIP}
    print(f"{name[:52]:52s} size {res[rel]['size']} shift {hi:+.2f}, {cover:.0%} over the plate{'  (flipped)' if name in FLIP else ''}{'  (no belt fit)' if 'Hip L' not in d.get('fits', {}) else ''}")
json.dump(res, open(OUT, "w"), indent=0)
