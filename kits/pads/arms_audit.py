import sys, json, collections, numpy as np, math
sys.path.insert(0, "/home/claude/kitbash/kits/pads")
from kb import *
TOR = BY["MarFil Assault - Torso 1"]
F62 = fit(BY["MarFil Assault - Shoulder Pad 1"], "Pad R")
def seat(a):
    """62's pose in the torso frame on arm a, brought to the right side."""
    side = "R" if fit(a, "Shoulder R") is not None and sock(a, "Pad R") is not None else "L"
    S = sock(TOR, "Shoulder " + side) @ fit(a, "Shoulder " + side) @ sock(a, "Pad " + side)
    if side == "L": S = conj(S)          # mirror into the right side (torso symmetric)
    return S @ F62, side
P0, _ = seat(BY["MarFil Assault - Arm 1A R"])
R0 = rot(P0); c0 = P0[:3, 3]
rows = []
for a in P:
    if a["type"] != "Arms" or not any(s["t"] in ("Pad R", "Pad L") for s in a.get("sockets", [])): continue
    if fit(a, "Shoulder R") is None and fit(a, "Shoulder L") is None: continue
    W, side = seat(a); R = rot(W)
    Rr = R @ R0.T                                   # world rotation from the reference seat
    tilt = math.degrees(math.acos(np.clip(Rr[:, 0] @ [1, 0, 0], -1, 1)))     # how far the shoulder axis moved
    swing = math.degrees(math.atan2(Rr[2, 1], Rr[1, 1]))                      # turn about X (arm swing)
    total = ang(Rr)
    sh = sock(TOR, "Shoulder R")[:3, 3]
    rows.append(dict(name=a["name"], maker=a["maker"], kit=a["kit"], side=side, id=a["id"], tilt=tilt, swing=swing, total=total,
                     dpos=float(np.linalg.norm(W[:3, 3] - c0)), src=[s for s in a["sockets"] if s["t"].startswith("Pad")][0].get("anchor", "")))
json.dump(rows, open("arms_audit.json", "w"), indent=0)
fam = collections.defaultdict(list)
for r in rows: fam[(r["maker"], r["kit"])].append(r)
print("%-58s %4s  %-22s %-22s %s" % ("family", "n", "tilt med [max]", "swing med [range]", "pad origin moved med"))
for k, v in sorted(fam.items(), key=lambda kv: -np.median([r["tilt"] for r in kv[1]])):
    t = [r["tilt"] for r in v]; s = [r["swing"] for r in v]; d = [r["dpos"] for r in v]
    print("%-58s %4d  %6.1f [%6.1f]       %6.1f [%6.1f..%6.1f]  %5.1f" % ((k[0] + "/" + k[1])[:58], len(v), np.median(t), max(t), np.median(s), min(s), max(s), np.median(d)))
