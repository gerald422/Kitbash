import json, glob, numpy as np
import spr_pads as SP, spr_pads2 as PA, capmatch as CM
from scipy.spatial import cKDTree
J = json.load(open("w/josh_pad_h4.json")); A = np.array(J["A_josh_torso"])
SW = {}; [SW.update(json.load(open(f))) for f in glob.glob("w/swing_*.json")]
R3 = np.array(SW["patternC arms/heavy weapons/patternC heavy Rarm 4.stl"]["R"])
R = np.eye(4); R[:3, :3] = R3; R[:3, 3] = CM.D0 - R3 @ CM.D0
Mref = np.linalg.inv(R) @ A
# how deep Josh's pad sits in the h4 shoulder armour
P, Pn = PA.normals_for("patternC arms/heavy weapons/patternC heavy Rarm 4.stl")
S = SP._pad_inner(); q = S @ (A[:3, :3] @ SP.F62[:3, :3]).T + A[:3, :3] @ SP.F62[:3, 3] + A[:3, 3]
d, i = cKDTree(P).query(q); sg = ((q - P[i]) * Pn[i]).sum(1)
frac = float(np.mean(sg < -0.15)); deep = float(-np.quantile(sg, 0.005))
print("Josh's pad on h4: %.1f%% of pad points >0.15 mm inside the arm, deepest ~%.2f mm; gap to arm median %.2f mm" % (100 * frac, deep, np.median(np.abs(sg))))
json.dump({"M": Mref.tolist(), "frac": frac}, open("w/josh_ref.json", "w"))
