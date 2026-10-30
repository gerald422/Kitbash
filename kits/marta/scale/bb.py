import sys; sys.path.insert(0, '/home/claude/real')
import fitlib as F, numpy as np
U = "/mnt/user-data/uploads/new cults/"
M = U + "Marta/51 May 2026-20260612T074408Z-3-001/51 May 2026/"
files = {
 'marta torso_1': M + "torso and back pack/torso_1.stl",
 'marta legs_1': M + "legs-chin pads and base/legs_1.stl",
 'marta set_arms_1': M + "amrs and weapons/set_arms_1_with_weapon_1.stl",
 'marta arm_2': M + "amrs and weapons/arm_2.stl",
 'marta closed_hand': M + "amrs and weapons/closed_hand.stl",
 'marta hand_1': M + "amrs and weapons/hand_1.stl",
 'mf vet chest 1': U + "All Mar All the time/VeteranBladeSquad/VeteranBladeSquad/Body/Body-RawSTL/17-Chest-1.stl",
 'mf vet legs 1B': U + "All Mar All the time/VeteranBladeSquad/VeteranBladeSquad/Body/Body-RawSTL/20-Legs-1-B-Corrected.stl",
}
for k, f in files.items():
    V, T = F.stl(f); lo, hi = V.min(0), V.max(0)
    print('%-18s tris %7d  min %s  max %s  size %s' % (k, len(T), lo.round(1), hi.round(1), (hi - lo).round(2)))
