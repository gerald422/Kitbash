import sys, json
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
IV = "/mnt/user-data/uploads/new cults/Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
out = json.load(open('/home/claude/kits/iv2/hands.json'))
for rel in ["Hands-Raw/Hand-Left/273-Hand-1-L.stl", "Hands-Raw/Hand-Left/274-Hand-2-L.stl", "Hands-Raw/Hand-Left/282-Hand-10-L.stl"]:
    V, Tr = T.read_stl_np(IV + rel); caps = T.hand_caps(V, Tr)
    M, md = T.hand_wrist_frame(V, Tr, 'L', T._bvh_nearest(V, Tr), caps); M = np.asarray(M)
    out[rel] = {'M': M.tolist(), 'med': md, 'caps': len(caps)}
    print('%-40s L fist %.3f  o %s  X %s Y %s  Z %s det %.0f' % (rel.split('/')[-1], md, np.round(M[:3, 3], 2), np.round(M[:3, 0], 2), np.round(M[:3, 1], 2), np.round(M[:3, 2], 2), np.linalg.det(M[:3,:3])), flush=True)
json.dump(out, open('/home/claude/kits/iv2/hands.json', 'w'), indent=1)
M = np.array(out["Hands-Raw/274-Hand-2-R.stl"]['M']); MX = np.diag([-1.0, 1, 1, 1])
print('MX Wr MX for 274:', np.round((MX @ M @ MX)[:3], 2).tolist())
