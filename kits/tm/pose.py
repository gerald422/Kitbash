"""Techmarine arm sets: each was exported on a turned torso; the pose of that torso from the two shoulder faces of the set."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np
inv = np.linalg.inv
R = json.load(open('/home/claude/kits/tm/rules.json'))['discs']
J = np.array([5.484, 0.202, 31.949]); NR = np.array([-1, 0, -0.04]); NR /= np.linalg.norm(NR); JL = J * [-1, 1, 1]; NL = NR * [-1, 1, 1]
def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0); H = (A - ca).T @ (B - cb); U, S, Vt = np.linalg.svd(H); d = np.sign(np.linalg.det(Vt.T @ U.T))
    Rm = Vt.T @ np.diag([1, 1, d]) @ U.T; return Rm, cb - Rm @ ca
def shoulder(name, side):
    # the shoulder face: the disc facing the torso (n ~ -x for a right arm, +x for a left), nearest the kit joint
    ds = [(np.array(d['c']), np.array(d['n'])) for d in R[name]]
    jj, nn = (J, NR) if side == 'R' else (JL, NL)
    ds = [d for d in ds if d[1] @ nn > 0.5]
    return min(ds, key=lambda d: np.linalg.norm(d[0] - jj))
SETS = {'a': ('18-Arm-4-R.stl', '12-Arm-1-L.stl'), 'b': ('19-Arm-5-R.stl', '16-Arm-3-L.stl'), 'c': ('20-DoubleArm-1.stl', '20-DoubleArm-1.stl'), 'd': ('22-DoubleArm-2.stl', '22-DoubleArm-2.stl')}
out = {}
for k, (r, l) in SETS.items():
    cr, nr = shoulder(r, 'R'); cl, nl = shoulder(l, 'L'); s = 3.0
    A = np.array([J, JL, J + s * NR, JL + s * NL]); B = np.array([cr, cl, cr + s * nr, cl + s * nl])
    Rm, t = kabsch(A, B); res = np.linalg.norm(A @ Rm.T + t - B, axis=1)
    out[k] = {'P': geo.M4(Rm, t).tolist(), 'R': r, 'L': l, 'cR': cr.tolist(), 'cL': cl.tolist()}
    print('set %s (%s + %s): torso turned %.1f deg, moved %s; disc residuals %s' % (k, r, l, geo.ang(Rm), np.round(t + Rm @ J - J, 2), np.round(res, 3)))
c14, n14 = shoulder('14-Arm-2-L.stl', 'L'); print('14-Arm-2-L shoulder vs 12-Arm-1-L: %.3f mm' % np.linalg.norm(c14 - np.array(out['a']['cL'])))
out['14'] = {'cL': c14.tolist()}
json.dump(out, open('/home/claude/kits/tm/pose.json', 'w'), indent=1)
