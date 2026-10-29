"""Intercessors V2: hand rule on the separate hands and the hand-held parts -> are they all in one wrist frame?"""
import sys, json, os, time
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
IV = "/mnt/user-data/uploads/new cults/Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
files = [f"Hands-Raw/{n}" for n in sorted(os.listdir(IV + "Hands-Raw")) if n.endswith('.stl')]
files += ["Melee-Handed-Raw/223-ChainSword-A-R.stl", "Melee-Handed-Raw/226-PowerAxe-1-A-R.stl", "Melee-Handed-Raw/241-PowerSword-A-R.stl", "Melee-Handed-Raw/232-PowerHammer-1-A-R.stl",
          "Weapons-Raw/219-BoltPistol-R.stl", "Weapons-Raw/221-PlasmaPistol-R.stl", "Bolter-Individual-Raw/144-Bolter-A-4-R.stl", "Bolter-Individual-Raw/172-Bolter-A-8-R.stl"]
out = {}
for rel in files:
    t0 = time.time()
    V, Tr = T.read_stl_np(IV + rel); caps = T.hand_caps(V, Tr)
    M, md = T.hand_wrist_frame(V, Tr, 'R', T._bvh_nearest(V, Tr), caps)
    out[rel] = None if M is None else {'M': np.asarray(M).tolist(), 'med': md, 'caps': len(caps)}
    if M is None: print('%-45s no frame (caps %d)' % (rel, len(caps)), flush=True); continue
    M = np.asarray(M)
    print('%-45s fist %.3f caps %d  o %s  Y %s  Z %s  %.0fs' % (rel, md, len(caps), np.round(M[:3, 3], 2), np.round(M[:3, 1], 2), np.round(M[:3, 2], 2), time.time() - t0), flush=True)
json.dump(out, open('/home/claude/kits/iv2/hands.json', 'w'), indent=1)
