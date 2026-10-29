import sys, json, zlib, base64, re, numpy as np, geo
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rr
src = open('/home/claude/tiow_blender/tiow_inbox.py').read()
i = src.index('_REFS_PACKED = ('); j = src.index(')', i)
ref = json.loads(zlib.decompress(base64.b64decode("".join(re.findall(r'"([^"]*)"', src[i:j+1])))))['Pad'][0]
region = np.array(ref['region']).reshape(-1, 3); P = np.array(ref['points']).reshape(3, 3); rj = np.array(ref['joint'])
side = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
def joint_of(rel):
    for k, m in side[rel]['fits'].items():
        if k.startswith('Shoulder'): return np.linalg.inv(np.array(m).reshape(4, 4))[:3, 3], k[-1]
def best_match(rel):
    j, sd = joint_of(rel)
    reg = region.copy(); PP = P.copy(); r_j = rj.copy()
    if sd == 'L': reg[:, 0] *= -1; PP[:, 0] *= -1; r_j[0] *= -1
    V, T = geo.load(rel); S = geo.surf(V, T, 300000); S = S[np.linalg.norm(S - j, axis=1) < 12]; tree = cKDTree(S)
    rng = np.random.default_rng(1); tiny = reg[rng.choice(len(reg), 120, replace=False)]
    Rs = Rr.random(4000, random_state=2).as_matrix()
    Rs = [R for R in Rs if np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))) < 120]
    sc = []
    for R in Rs:
        t = j - R @ r_j; d = tree.query(tiny @ R.T + t)[0]; sc.append((np.median(d), R, t))
    sc.sort(key=lambda x: x[0]); best = None
    for m, R, t in sc[:15]:
        R, t, d = geo.icp(reg, tree, S, R, t, 40)
        if best is None or np.median(d) < best[0]: best = (np.median(d), R, t)
    return best
for rel in sys.argv[1:]:
    m, R, t = best_match(rel)
    print('%-40s best median %.3f  swing %.1f deg' % (rel.split('/')[-1], m, geo.ang(R)))
