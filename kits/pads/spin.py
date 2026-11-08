"""Spin of a pad seat about its outward axis (cup centre -> pad), measured from the torso's front. 0 = Josh's Springles seats."""
import sys, json, collections, numpy as np, math
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from cupcheck import *
def axes(seat):
    W = seat @ F56; c = xf(W, C56[None])[0]; m = xf(W, M56[None])[0]; o = (m - c) / np.linalg.norm(m - c)
    return c, o
def spin_of(seat):
    c, o = axes(seat); y = rot(seat)[:, 1]; y = y - (y @ o) * o; y /= np.linalg.norm(y)
    f = np.array([0, 1.0, 0]); f = f - (f @ o) * o; f /= np.linalg.norm(f)
    return math.degrees(math.atan2(np.cross(f, y) @ o, f @ y))
rows = []
for a in P:
    if a["type"] != "Arms" or not any(s["t"].startswith("Pad") for s in a.get("sockets", [])): continue
    if fit(a, "Shoulder R") is None and fit(a, "Shoulder L") is None: continue
    side, S, V, T = arm_world(a); rows.append(dict(name=a["name"], fam=a["maker"] + "/" + a["kit"], spin=spin_of(cur_seat(a, S, side))))
SP0 = float(np.median([r["spin"] for r in rows if r["fam"].startswith("Springles")]))
def dspin(x): return (x - SP0 + 180) % 360 - 180
if __name__ == "__main__":
    for r in rows: r["d"] = dspin(r["spin"])
    json.dump(dict(SP0=SP0, rows=rows), open("spin.json", "w"))
    b = {r["name"]: r for r in rows}
    for n in ["MarFil Assault - Arm 1A R", "MarFil Intercessor - Arm 1 L", "MarFil Intercessor - Arm 5 L", "BBoosty Medusas Mortals - Arm 2 R", "TN Mk7-8 Assault - Mk7 Power Fist B1", "MarFil Intercessor - Bolter C3 R", "MarFil Intercessor - Bolter A Grenade 3 L", "MarFil Assault - Arm 7B R"]:
        print("%-45s spin off %6.1f" % (n, b[n]["d"]))
    fam = collections.defaultdict(list)
    for r in rows: fam[r["fam"]].append(r["d"])
    for k, v in sorted(fam.items()):
        v = np.array(v); print("%-32s n=%3d spin off med %6.1f  |off| p90 %5.1f  n>45: %3d" % (k[:32], len(v), np.median(v), np.percentile(abs(v), 90), (abs(v) > 45).sum()))
