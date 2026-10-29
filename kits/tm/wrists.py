"""Techmarine left arms: their wrist faces stray 15-18 % from round (the rule takes 12 %) - the wrist rule at 20 %, saved."""
import sys, json, os
import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
U = "/mnt/user-data/uploads/new cults/All Mar All the time/"
PAR = json.load(open('/home/claude/kits/tm/tm_partial.json'))['side']
out = {}
for b in ('12-Arm-1-L', '14-Arm-2-L', '16-Arm-3-L', '18-Arm-4-R', '19-Arm-5-R'):
    rel = 'Techmarine (2)/Techmarine/Arms/Arms-Raw-STL/' + b + '.stl'; sd = b[-1]
    joint = np.linalg.inv(np.array(PAR[rel]['fits']['Shoulder ' + sd]).reshape(4, 4))[:3, 3]
    V, Tr = T.read_stl_np(U + rel); V = np.asarray(V, float); Tr = np.asarray(Tr)
    W0 = T.arm_wrist_frame(V, Tr, joint, sd); W = T.arm_wrist_frame(V, Tr, joint, sd, round_tol=0.2)
    out[rel] = None if W is None else np.asarray(W).tolist()
    print(b, 'rule:', None if W0 is None else np.round(np.asarray(W0)[:3, 3], 2), ' at 20 %:', None if W is None else np.round(np.asarray(W)[:3, 3], 2), flush=True)
json.dump(out, open('/home/claude/kits/tm/wrists.json', 'w'), indent=1)
