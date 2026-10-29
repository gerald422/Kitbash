"""Write the Springles arm sidecars (stage dir mirrors D:\\new cults\\Springles)."""
import sys, json, os, numpy as np
from cuprule import roll_Z
from spr_arms import S_R, S_L
OUT = "/home/claude/kits/out113/stage_spr/Springles/"
AF = json.load(open("arm_fits.json")); C = json.load(open("cups.json")); CT = json.load(open("cups_transfer.json"))
def L16(M): return [round(float(x), 6) for x in np.asarray(M).ravel()]
n = 0; stats = []
for rel, a in sorted(AF.items()):
    side = a["joint"][-1]; S = S_R if side == "R" else S_L; Fm = np.array(a["fit"])
    socks = []
    cupM = C.get(rel, {}).get("M") or CT.get(rel, {}).get("M")
    if cupM is not None:
        M = np.array(cupM); Y = M[:3, 1] / np.linalg.norm(M[:3, 1])
        W = S @ Fm; Zt = roll_Z(W[:3, :3] @ Y); Z = W[:3, :3].T @ Zt; Z -= (Z @ Y) * Y; Z /= np.linalg.norm(Z)
        M2 = np.eye(4); M2[:3, 0], M2[:3, 1], M2[:3, 2], M2[:3, 3] = np.cross(Y, Z), Y, Z, M[:3, 3]
        how = "Springles wrist cup: lip centre, Y into the arm" + ("" if rel in C else " (carried from the same pose in pattern C)")
        socks.append({"type": "Hand " + side, "name": os.path.basename(rel)[:-4] + "_socket_Hand " + side, "matrix": L16(M2),
                      "display_type": "ARROWS", "display_size": 3.0, "props": {"tiow_from": how}})
    d = {"schemaVersion": 1, "part": os.path.basename(rel)[:-4], "category": "Arms", "scale": a["scale"], "noPad": True,
         "sockets": socks, "fits": {a["joint"]: L16(Fm)},
         "notes": {"Shoulder": "heresy scale (Josh's working file); shoulder disc centre on Josh's HeresyArms_r point, file axes",
                   "Hand": "cup at the wrist; hands with the Springles dome wrist seat in it" if socks else "hand built in"}}
    p = OUT + rel[:-4] + ".sockets.json"; os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, "w")); n += 1
print(n, "arm sidecars;", sum(1 for r in AF if (r in C or r in CT)), "with a Hand socket")
