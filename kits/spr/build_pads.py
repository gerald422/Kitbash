"""Write Pad R/L anchors into the Springles arm sidecars (reference anchor on the slung arm, turned by each arm's
shoulder rotation, pushed out to clear its shoulder)."""
import sys, json, glob, os, numpy as np
import capmatch as CM, spr_pads as SP, spr_pads2 as PA
from spr_arms import S_R, S_L
ST = SP.ST
SW = {}
for f in glob.glob("w/swing_*.json"): SW.update(json.load(open(f)))
Mref = PA.ref()[1] if len(sys.argv) < 2 else np.array(json.load(open(sys.argv[1]))["M"])
MX = np.diag([-1.0, 1, 1, 1])
FROM = ("Josh's 62 on patternC heavy Rarm 4 (actual.blend, 20 Oct), turned with this arm's shoulder (match %.2f mm), clear of its armour" if len(sys.argv) > 1
        else "Josh's 62-on-76 pad on the Springles slung arm, turned with this arm's shoulder (match %.2f mm), clear of its armour")
rep = []
for rel, sw in sorted(SW.items()):
    R3 = np.array(sw["R"]); R = np.eye(4); R[:3, :3] = R3; R[:3, 3] = CM.D0 - R3 @ CM.D0
    M = R @ Mref
    Pp, Pn = PA.normals_for(rel); d = PA.dirv(M)
    t = SP.push_out(Pp, Pn, M, d); M[:3, 3] += t * d
    side = sw["side"]
    if side == "L": M = MX @ M @ MX
    p = ST + rel[:-4] + ".sockets.json"; s = json.load(open(p))
    W = (S_R if side == "R" else S_L) @ np.array(s["fits"]["Shoulder " + side]).reshape(4, 4)
    Mp = np.linalg.inv(W) @ M
    s["sockets"] = [x for x in s["sockets"] if not x["type"].startswith("Pad ")]
    s["sockets"].append({"type": "Pad " + side, "name": os.path.basename(rel)[:-4] + "_socket_Pad " + side, "matrix": [round(float(x), 6) for x in Mp.ravel()],
                         "display_type": "ARROWS", "display_size": 3.0,
                         "props": {"tiow_anchor": "copied", "tiow_from": FROM % sw["median"]}})
    s["noPad"] = False
    s.get("notes", {}).pop("Pad", None)
    json.dump(s, open(p, "w")); rep.append((rel, sw["median"], t))
    if "heavy Rarm 4" in rel and "patternC" in rel: print("C heavy Rarm 4 push", t, flush=True)
print(len(rep), "pad anchors; worst shoulder matches:", sorted(rep, key=lambda r: -r[1])[:5])
