"""Straighten a part that sits slanted in its own file: snap hol_orient's axes to the part's principal axes
(the nearest one each, same signs).  python hol_pca.py NAME PARTS_JSON ORIENT_JSON (updated in place)"""
import sys, json, numpy as np; sys.path.insert(0, __file__.rsplit("/", 1)[0]); from hol_common import *
nm, parts, oj = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]; O = json.load(open(oj))
rel = [r for r in parts if r.split("\\")[-1][:-4] == nm][0]; V, T = stl(U + rel.replace("\\", "/")); P, _ = surf(V, T, 40000)
w, E = np.linalg.eigh(np.cov((P - P.mean(0)).T)); R = np.array(O[nm])
y = E[:, np.argmax(np.abs(E.T @ R[1]))]; y *= np.sign(y @ R[1])
z = R[2] - y * (R[2] @ y); z /= np.linalg.norm(z); x = np.cross(y, z)
O[nm] = np.array([x, y, z]).tolist(); json.dump(O, open(oj, "w"))
print(nm, "turned %.1f deg" % np.degrees(np.arccos(np.clip(y @ R[1], -1, 1))))
