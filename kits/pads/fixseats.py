"""Arm Pad sockets: flag seats outside the range of Josh's Springles seats and the Mar Fil Assault seats he has used
(spin about the cup axis, how far the pad points out from the side, how far it leans along the upper arm), and give each
flagged arm the seat of the passing arm in the nearest pose (same family first), turned about the shoulder joint by the
pose difference."""
import sys, json, math, collections, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from respin import *
def metrics(seat, u):
    c, o = axes(seat); sp = dspin(spin_of(seat))
    return dict(spin=sp, out=math.degrees(math.acos(np.clip(o[0], -1, 1))), lift=math.degrees(math.acos(np.clip(o @ -u, -1, 1))))
def passes(m): return abs(m["spin"]) <= 45 and 50 <= m["out"] <= 110 and 30 <= m["lift"] <= 85
ARMS = []
for a in P:
    if a["type"] != "Arms" or not any(s["t"].startswith("Pad") for s in a.get("sockets", [])): continue
    if fit(a, "Shoulder R") is None and fit(a, "Shoulder L") is None: continue
    side, S, V, T = arm_world(a); u = updir3(V); seat = cur_seat(a, S, side)
    ARMS.append(dict(a=a, side=side, S=S, u=u, seat=seat, m=metrics(seat, u), fam=a["maker"] + "/" + a["kit"]))
GOOD = [x for x in ARMS if passes(x["m"]) and x["a"]["maker"] not in ("BBoosty", "CyberBrush")]
def predict(x, exclude_self=True):
    pool = [g for g in GOOD if not (exclude_self and g is x)]
    best = max(pool, key=lambda g: g["u"] @ x["u"] + (0.03 if g["fam"] == x["fam"] else 0.0))
    R = np.eye(4); R[:3, :3] = rmin(best["u"], x["u"])
    return about_J(R) @ best["seat"], best
if __name__ == "__main__":
    err = collections.defaultdict(list)
    for g in GOOD:
        W, b = predict(g); err[g["fam"]].append(ang(rot(W) @ rot(g["seat"]).T))
    print("leave-one-out on passing arms (deg):")
    for k, v in sorted(err.items()):
        if len(v) >= 5: print("   %-30s n=%3d med %5.1f p90 %5.1f" % (k[:30], len(v), np.median(v), np.percentile(v, 90)))
    fl = collections.Counter(); tot = collections.Counter()
    for x in ARMS:
        tot[x["fam"]] += 1
        if not passes(x["m"]): fl[x["fam"]] += 1
    print("flagged %d of %d" % (sum(fl.values()), len(ARMS)))
    print(", ".join("%s %d/%d" % (k, fl[k], tot[k]) for k in sorted(tot)))
