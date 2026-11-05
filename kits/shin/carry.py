"""Carry Josh's shin pad placements to the proposed Marta legs: each reference shin patch (legs points near his pad, torso
coords; mirrors in X for the other side) is matched onto the target legs' lower leg on that side by rigid ICP from a grid
of starts; best match wins; socket = match @ reference socket. python carry.py OUT.json [i0 i1]"""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kitbash/kits/plates'); from hol_common import stl, tf, M16
from legs_frame import legs as legs_geo
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
from reg import sicp
U = '/mnt/user-data/uploads/d/Kitbash Library/'; L = '/home/claude/kitbash/library/'
D = json.load(open('placed.json')); S = json.load(open('sockets_ref.json')); props = json.load(open('proposed.json'))
i0, i1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, len(props))
Mx = np.diag([-1., 1, 1, 1]); Dx = np.diag([-1., 1, 1, 1]); rng = np.random.default_rng(0)
refs = {'R': [], 'L': []}
for key, r in D.items():
    _, V, T, M = legs_geo(r['legs'], U); Vt = tf(M, V); PV, _ = stl(U + r['pad'] + '.stl'); Q = tf(M @ np.array(r['pad_in_legs']), PV)
    d, _ = cKDTree(Q).query(Vt); patch = Vt[d < 4.0]; patch = patch[rng.choice(len(patch), min(len(patch), 2500), replace=False)]
    So = np.array(S[key]['socket_torso']); nm = key.split('|')[0].replace('Marta ', '')
    refs[r['side']].append((nm + ' ' + r['side'], patch, So))
    refs['L' if r['side'] == 'R' else 'R'].append((nm + ' ' + r['side'] + ' mirrored', tf(Mx, patch), Mx @ So @ Dx))
starts = [Rot.from_euler('xy', (a, b), degrees=True).as_matrix() for a in range(-60, 61, 20) for b in (-20, 0, 20)]
out = {}
for k in props[i0:i1]:
    _, V, T, M = legs_geo(k, U); Vt = tf(M, V); z0, z1 = Vt[:, 2].min(), Vt[:, 2].max(); res = {}
    for s, sx in (('R', 1), ('L', -1)):
        tgt = Vt[(Vt[:, 0] * sx > -1.0) & (Vt[:, 2] < z0 + 0.7 * (z1 - z0))]; tgt = tgt[rng.choice(len(tgt), min(len(tgt), 60000), replace=False)]
        best = None
        for nm, patch, So in refs[s]:
            c = patch.mean(0)
            for R0 in starts:
                t0 = c - R0 @ c
                R, t, sc, med, p95 = sicp(patch, tgt, R0, t0, 1.0, it=30, scale=False)
                if best is None or med < best[0]: best = (med, p95, nm, R, t, So)
        med, p95, nm, R, t, So = best; R, t, sc, med, p95 = sicp(refs[s][[x[0] for x in refs[s]].index(nm)][1], tgt, R, t, 1.0, it=80, scale=False)
        A = np.eye(4); A[:3, :3], A[:3, 3] = R, t; Sk = np.linalg.inv(M) @ A @ So
        res[s] = {'ref': nm, 'median': round(float(med), 3), 'p95': round(float(p95), 3), 'socket_file': Sk.tolist(), 'socket_torso': (A @ So).tolist()}
    out[k] = res; print('%-48s R: %-34s %.3f / %.3f | L: %-34s %.3f / %.3f' % (k.split('/')[-1][:48], res['R']['ref'], res['R']['median'], res['R']['p95'], res['L']['ref'], res['L']['median'], res['L']['p95']), flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=0)
