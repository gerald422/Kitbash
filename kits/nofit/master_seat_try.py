"""Trial (Nov 14, notes 094): seat every pad of a maker on ONE master pad's inside (Josh's idea: a shell from a fitted
piece per maker and part type, every other part mated to it, its fit taken from that).
    blender --background --factory-startup --python master_seat_try.py -- MASTER_REL MAKER_PREFIX [LIBRARY]"""
import sys, os, json, glob
import numpy as np
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, REPO)
from kb import carry, geo
A = sys.argv[sys.argv.index("--") + 1:]; MREL, PREFIX = A[0], A[1]; LIB = (A[2] if len(A) > 2 else "D:/Kitbash Library").rstrip("/") + "/"
def load(rel):
    sc = json.load(open(LIB + rel + ".sockets.json", encoding="utf-8-sig")); return sc, carry.Inner(carry.Shape(LIB + rel + ".stl", sc.get("scale", 1.0)))
def q90(tree, P): return float(np.quantile(tree.query(P)[0], 0.9))
def seat(M, P, R0):
    """the master's inside M put on the part's inside P, starting with the boxes lined up after the turn R0"""
    t = (P.S.min(0) + P.S.max(0)) / 2 - R0 @ ((M.S.min(0) + M.S.max(0)) / 2)
    for _ in range(25):                                    # slide on, no turning
        d, i = P.tree.query(M.full @ R0.T + t); k = d <= np.quantile(d, 0.85); t = t + (P.tree.data[i[k]] - (M.full[k] @ R0.T + t)).mean(0)
    R, t, _ = geo.icp(M.full, P.tree, R0, t, 30)           # then settle (may turn a little)
    s = max(q90(P.tree, M.full @ R.T + t), q90(M.tree, (P.full - t) @ R))
    return s, R, t
msc, M = load(MREL); side = next(iter(msc["fits"])); FM = np.array(msc["fits"][side]).reshape(4, 4)
print("master %s (%s), inside %d points, box %s" % (os.path.basename(MREL), side, len(M.S), M.ext.round(2)))
rows = []
for f in sorted(glob.glob(glob.escape(LIB + PREFIX) + "/**/Shoulder Pads/*.sockets.json", recursive=True)):
    rel = f[len(LIB):-13].replace("\\", "/")
    if rel == MREL or not os.path.exists(LIB + rel + ".stl"): continue
    try: sc, P = load(rel)
    except Exception as e: print("unreadable", rel, e); continue
    s, R, t = seat(M, P, np.eye(3)); how = "frame"
    if s > 0.5:                                            # not lying as the master does: the square turns whose box fits
        c = sorted(carry.ROTS, key=lambda R0: float(np.abs(np.ptp(M.S @ R0.T, 0) - np.ptp(P.S, 0)).sum()))[:6]
        alt = min((seat(M, P, R0) for R0 in c), key=lambda x: x[0])
        if alt[0] < s - 0.1: s, R, t = alt; how = "turned"
    F = FM @ np.linalg.inv(carry.M4(R, t)); lib = sc.get("fits") or {}
    cmp_ = ""
    if side in lib:
        T = np.array(lib[side]).reshape(4, 4); cmp_ = "library: %.2f mm %.1f deg" % (float(np.linalg.norm(carry.point("fit", F) - carry.point("fit", T))), carry.ang(F, T))
    elif lib: cmp_ = "library has %s" % list(lib)
    else: cmp_ = "no fit yet"
    rows.append((s, rel, cmp_)); print("%-52s seat %.2f mm, settled %4.1f deg (%s)  %s" % (os.path.basename(rel)[-52:], s, geo.ang(R), how, cmp_), flush=True)
