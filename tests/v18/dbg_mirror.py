import bpy, sys, json, time, os, cProfile, pstats
import numpy as np
import importlib.util
spec = importlib.util.spec_from_file_location('ti', '/home/claude/tiow_blender/tiow_inbox.py'); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
RAW = '/home/claude/raw/VeteranSquad/VeteranSquad/'
MX = np.diag([-1.0, 1, 1, 1])
def ang(R): return np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
VR, TR = T.read_stl_np(RAW + 'Melee/Melee-RawSTL/132-Sword-B.stl'); VL, TL = T.read_stl_np(RAW + 'Melee/Melee-Mirrored/132-Sword-B-Mirrored.stl')
pr = cProfile.Profile(); pr.enable()
HR, mR = T.hand_wrist_frame(VR, TR, 'R')
pr.disable(); pstats.Stats(pr).sort_stats('cumulative').print_stats(12)
HL, mL = T.hand_wrist_frame(VL, TL, 'L')
print('fist R %.3f L %.3f' % (mR, mL))
D = np.linalg.inv(MX @ HR @ MX) @ HL
print('H_L vs mirror(H_R): %.2f deg %.3f mm' % (ang(D[:3, :3]), np.linalg.norm(D[:3, 3])))
print('HR\n', HR.round(3), '\nHL\n', HL.round(3))
ML, mLL = T.hand_wrist_frame(VR, TR, 'L'); print('R sword tried as a left hand: fist %.3f' % mLL)
for nm in ('142-Arm-A',):
    VaR, TaR = T.read_stl_np(RAW + 'Arms/Arms-RawSTL/%s.stl' % nm); VaL, TaL = T.read_stl_np(RAW + 'Arms/Arms-Mirrored/%s-Mirrored.stl' % nm)
    AR = T.arm_wrist_frame(VaR, TaR, [5.48, 0.2, 31.95], 'R'); AL = T.arm_wrist_frame(VaL, TaL, [-5.48, 0.2, 31.95], 'L')
    D = np.linalg.inv(MX @ AR @ MX) @ AL; print('arm A_L vs mirror(A_R): %.2f deg %.3f mm' % (ang(D[:3, :3]), np.linalg.norm(D[:3, 3])))
