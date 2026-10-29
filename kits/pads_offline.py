"""Pad R/L anchors for every Assault arm and power fist: Josh's 76-Arm-1-R-A mini shoulder pad matched onto
each arm over all swings about its (known) shoulder joint, three points carried, frame as the add-on builds it."""
import json, numpy as np, geo, os, sys
from scipy.spatial import cKDTree
from padcheck import best_match, region, P, rj, joint_of, side
LIMIT = 0.22
out, report = {}, []
rels = sorted(r for r, d in side.items() if d.get('category') == 'Arms')
for rel in rels:
    j, sd = joint_of(rel)
    m, R, t = best_match(rel)
    PP = P.copy()
    if sd == 'L': PP[:, 0] *= -1
    pts = PP @ R.T + t
    V, T = geo.load(rel); S = geo.surf(V, T, 1500000); tree = cKDTree(S)
    pts = S[tree.query(pts)[1]]                      # onto the surface, like closest_point_on_mesh
    a, b, c = pts; line = (b - a) / np.linalg.norm(b - a); mid = (a + b) / 2
    off = (c - mid) - line * ((c - mid) @ line); y = line; z = off / np.linalg.norm(off); x = np.cross(y, z)
    if x[0] < 0: x, y = -x, -y                          # X out on a right arm, in on a left: +X of the file either way
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, c
    dims = V.max(0) - V.min(0)
    report.append((os.path.basename(rel), sd, m))
    if m > LIMIT: continue
    out[rel] = {'type': f'Pad {sd}', 'name': f"{os.path.basename(rel)[:-4]}_socket_Pad {sd}", 'matrix': [float(v) for v in M.reshape(-1)],
                'display_type': 'ARROWS', 'display_size': float(0.15 * dims.max()),
                'props': {'tiow_anchor': 'copied', 'tiow_from': '76-Arm-1-R-A'}, 'points': pts.tolist()}
    print('%-30s %s median %.3f' % (os.path.basename(rel), sd, m), flush=True)
json.dump({'anchors': out, 'report': report}, open('/home/claude/kits/pads_offline.json', 'w'))
print('done', len(out), 'of', len(rels), 'rejected', [r for r in report if r[2] > LIMIT])
