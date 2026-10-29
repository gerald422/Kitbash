"""Device: TN helmets -> Neck fit (neck ball in the reference torso's cup, upright, facing front). usage: tn_helmets.py out.json"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.expanduser('~/ctools'))
from stllib import stl
REF = {"Mk2": [[-0.999988, -0.004291, 0.00215, 0.005052], [0.004781, -0.929758, 0.36814, -0.314407], [0.00042, 0.368146, 0.929768, 3.008875], [0.0, 0.0, 0.0, 1.0]], "Mk3": [[-0.999988, -0.004463, 0.002226, 0.007281], [0.004969, -0.929758, 0.368139, -0.292977], [0.000427, 0.368145, 0.929768, 2.980502], [0.0, 0.0, 0.0, 1.0]], "Mk4": [[-0.99999, -0.004081, 0.001961, 0.014767], [0.004517, -0.929764, 0.368128, -0.325454], [0.000321, 0.368134, 0.929773, 3.014148], [0.0, 0.0, 0.0, 1.0]], "Mk6": [[-0.99999, -0.004511, 4.6e-05, -0.004865], [0.004211, -0.929761, 0.36814, -0.80187], [-0.001618, 0.368137, 0.92977, 3.218137], [0.0, 0.0, 0.0, 1.0]], "Mk6A": [[-0.999989, -0.004653, 1.7e-05, 0.007144], [0.004333, -0.929758, 0.368145, -0.235604], [-0.001697, 0.368141, 0.929768, 3.069837], [0.0, 0.0, 0.0, 1.0]], "Mk7": [[-0.99999, -0.004523, 0.000209, -0.007492], [0.004283, -0.929763, 0.368133, -0.557425], [-0.001471, 0.36813, 0.929773, 3.215621], [0.0, 0.0, 0.0, 1.0]], "Mk8": [[-0.999989, -0.0046, -0.000228, -0.006227], [0.004193, -0.929762, 0.368136, -0.8081], [-0.001906, 0.368131, 0.929772, 3.200552], [0.0, 0.0, 0.0, 1.0]], "Mk10": [[-0.999979, -0.005266, -0.003829, -0.009442], [0.003486, -0.929756, 0.36816, 0.549753], [-0.005499, 0.368139, 0.929754, 3.299089], [0.0, 0.0, 0.0, 1.0]], "Mk7J": [[-0.999989, -0.004584, -0.000303, -0.004887], [0.004151, -0.929763, 0.368135, -0.750826], [-0.001969, 0.36813, 0.929772, 2.478362], [0.0, 0.0, 0.0, 1.0]]}
FOLD = {"TurtleNinja's Mk2-6 Builder/Mk2/Helmets": ("Mk2", [0, 0, -1]), "TurtleNinja's Mk2-6 Builder/Mk3/Helmets": ("Mk3", [0, 0, -1]),
        "TurtleNinja's Mk2-6 Builder/Mk4/Helmets": ("Mk4", [-1, 0, 0]), "TurtleNinja's Mk2-6 Builder/Mk5/Helmets": ("Mk4", [-1, 0, 0]),
        "TurtleNinja's Mk2-6 Builder/Mk6/Helmets": ("Mk6", [-1, 0, 0]), "TurtleNinja's Mk6 Addon 1/Updated Helmets": ("Mk6", [0, 0, -1]),
        "TurtleNinja's Mk7-8 Builder/Mk7-8/Helmets": ("Mk7", [-1, 0, 0]), "TurtleNinja's Mk4 Tactical Squad/Helmets": ("Mk4", [0, 0, -1])}
def frame(o, z, y):
    z = np.asarray(z, float); z /= np.linalg.norm(z); y = np.asarray(y, float); y = y - (y @ z) * z; y /= np.linalg.norm(y)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = np.cross(y, z), y, z, o; return M
def sphere(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); x = np.linalg.lstsq(A, b, rcond=None)[0]; c = x[:3]; r = np.sqrt(x[3] + c @ c)
    return c, r, float(np.sqrt(np.mean((np.linalg.norm(P - c, axis=1) - r) ** 2)))
root = os.path.expanduser("~/mnt/new cults/Turtle Ninja"); res = {}
for d, (fam, front) in FOLD.items():
    for f in sorted(os.listdir(os.path.join(root, d))):
        if not f.lower().endswith('.stl') or f.startswith('._'): continue
        rel = d + '/' + f
        try:
            F = stl(os.path.join(root, rel)); V = F.reshape(-1, 3); y0 = V[:, 1].min()
            P = np.unique(V[V[:, 1] < y0 + 1.8].round(4), axis=0)
            c, r, rms = sphere(P)
            Hb = frame(c, [0, 1, 0], front)
            fit = np.array(REF[fam]) @ np.linalg.inv(Hb)
            res[rel] = dict(fam=fam, ball=c.round(3).tolist(), r=round(float(r), 3), rms=round(rms, 4), fit=fit.round(6).tolist())
        except Exception as e:
            res[rel] = dict(err=repr(e))
json.dump(res, open(sys.argv[1], 'w'))
print(len(res), 'err', sum('err' in v for v in res.values()))
