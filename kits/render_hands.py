import sys; sys.path.insert(0, '/home/claude/kits')
import qr, numpy as np, json, os, ksheet
from fist import side as SIDE, Hof
import armcheck
A = json.load(open('/home/claude/kits/armrule_res.json')); H = json.load(open('/home/claude/kits/handrule_res.json'))
VS = json.load(open('/home/claude/kits/vs_rules.json'))
AM = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'; VB = 'VeteranSquad/VeteranSquad/'
def arm_rule(rel): return np.array((A.get(rel) or VS['arms'][rel])['M'])
def hand_rule(rel): return np.array((H.get(rel) or VS['hands'][rel])['M'])
josh_arm = {rel: S for rel, sd, S, j in armcheck.arm_items()}
def pair(name, arm, wpn, josh=False, sd='R'):
    Ar = arm_rule(arm); Wr = Ar @ np.linalg.inv(hand_rule(wpn))
    items = [(arm, np.eye(4), qr.GREY), (wpn, Wr, qr.ORANGE)]
    if josh: items.append((wpn, josh_arm[arm] @ np.linalg.inv(Hof(wpn, sd)), qr.BLUE))
    c = Ar[:3, 3]
    v = {'front': (0, 1, 0), 'side': (1 if sd == 'R' else -1, 0, 0), 'top': (0, 0, 1)}
    near = qr.run(name + '_n', items, views={'wrist': tuple(Ar[:3, 0])}, res=420, centre=c - 2 * Ar[:3, 1], size=12)
    wide = qr.run(name + '_w', items, views=v, res=420, centre=c - 4 * Ar[:3, 1], size=40)
    return [(near['wrist'], name + ' wrist'), (wide['front'], 'front'), (wide['side'], 'side'), (wide['top'], 'top')]
rows = [
    pair('amv2_77_175', AM + 'Arms/77-Arm-1-R-B.stl', AM + 'Melee/175-ChainSword-1-R.stl', josh=True),
    pair('amv2_91_193', AM + 'Arms/91-Arm-4-R-A.stl', AM + 'Melee/193-PowerHammer-A-1-R.stl', josh=True),
    pair('vs142_amv2_193', VB + 'Arms/Arms-RawSTL/142-Arm-A.stl', AM + 'Melee/193-PowerHammer-A-1-R.stl'),
    pair('amv2_77_vs130', AM + 'Arms/77-Arm-1-R-B.stl', VB + 'Melee/Melee-RawSTL/130-ChainSword-B.stl'),
    pair('vs143_vs135', VB + 'Arms/Arms-RawSTL/143-Arm-B.stl', VB + 'Melee/Melee-RawSTL/135-Hammer-A.stl'),
    pair('amv2_78_vs132L', AM + 'Arms/78-Arm-1-L-A.stl', VB + 'Melee/Melee-Mirrored/132-Sword-B-Mirrored.stl', sd='L'),
    pair('vs142L_amv2_175L', VB + 'Arms/Arms-Mirrored/142-Arm-A-Mirrored.stl', AM + 'Melee/LeftOrientated/175-ChainSword-1-L.stl', sd='L'),
]
ksheet.sheet(rows, '/home/claude/kits/renders/hands_rule.png', 300, 'Rule only: grey arm, orange weapon placed by wrist rules (blue = Josh\'s placement where he has one)')
