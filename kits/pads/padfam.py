import sys, json, collections, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from respin import *
# K: dome seat -> Josh's Springles seat in the same pose (BBoosty Medusas Arm 4 R <-> Springles P Melee Arm 1 R)
b = BY["BBoosty Medusas Mortals - Arm 4 R"]; sd, Sb, _, _ = arm_world(b); D = cur_seat(b, Sb, sd)
sp = BY["Springles Pattern P - Melee Arm 1 R"]; s2, S2, _, _ = arm_world(sp); WS = cur_seat(sp, S2, s2)
K = np.linalg.inv(D) @ WS
def pad_fit(p, convert=True):
    F = fit(p, "Pad R"); mir = False
    if F is None: F = conj(fit(p, "Pad L")); mir = True
    if convert and p["maker"] in ("BBoosty", "CyberBrush"): F = np.linalg.inv(K) @ F
    return F, mir
