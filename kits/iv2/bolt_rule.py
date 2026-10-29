import sys, json, os, time
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
IV = "/mnt/user-data/uploads/new cults/Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
BI = "Bolter-Individual-Raw/"; BL = BI + "Bolter-Individual-Left/"
out = {}
for rel, side in [(BI + "144-Bolter-A-4-R.stl", 'R'), (BI + "151-Bolter-A-5-R.stl", 'R'), (BI + "158-Bolter-A-6-R.stl", 'R'), (BI + "165-Bolter-A-7-R.stl", 'R'), (BI + "172-Bolter-A-8-R.stl", 'R'),
                  (BL + "144-Bolter-A-4-L.stl", 'L'), (BL + "172-Bolter-A-8-L.stl", 'L'), (BL + "144-Bolter-A-4-L.stl", 'R'), (BL + "172-Bolter-A-8-L.stl", 'R')]:
    V, Tr = T.read_stl_np(IV + rel); caps = T.hand_caps(V, Tr)
    M, md = T.hand_wrist_frame(V, Tr, side, T._bvh_nearest(V, Tr), caps)
    if M is None: print(rel, side, 'none'); continue
    M = np.asarray(M); out[rel + ':' + side] = {'M': M.tolist(), 'med': md}
    print('%-28s %s fist %.3f caps %d  o %s  Y %s  Z %s' % (rel.split('/')[-1], side, md, len(caps), np.round(M[:3, 3], 2), np.round(M[:3, 1], 2), np.round(M[:3, 2], 2)), flush=True)
json.dump(out, open('/home/claude/kits/iv2/bolt_rule.json', 'w'), indent=1)
