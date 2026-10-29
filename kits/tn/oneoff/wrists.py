"""bpyenv: wrist frames (the add-on's rule) for arms in a kit, in their own file frame. usage: wrists.py out.json path:side:jx,jy,jz ..."""
import sys, json, numpy as np, hashlib, os
sys.path.insert(0, '/home/claude/tiow_blender'); import tiow_inbox as TI
C = "/home/claude/kits/cache/abs_"
def load(path):
    key = hashlib.md5((path + str(os.path.getsize(path))).encode()).hexdigest(); z = np.load(C + key + ".npz"); return z["V"].astype(float), z["T"]
out = {}
for arg in sys.argv[2:]:
    p, side, j = arg.rsplit(':', 2); J = np.array([float(x) for x in j.split(',')])
    V, T = load(p); W = None
    for tol in (0.12, 0.2):
        W = TI.arm_wrist_frame(V, T, J, side, round_tol=tol)
        if W is not None: break
    out[p] = None if W is None else np.asarray(W).tolist(); print(os.path.basename(p), side, 'wrist' if W is not None else 'NONE')
json.dump(out, open(sys.argv[1], 'w'))
