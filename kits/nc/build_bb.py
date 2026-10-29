"""BBoosty sidecars, phase 1: arms (+ wrist Hand socket), hands, with-hand weapons, two-handed swords,
heads, backpacks.  -> /home/claude/kits/out114/stage_bb/BBoosty/<path>.sockets.json"""
import numpy as np, json, os, sys
from geo import *; from bbrules import *; from handfind import find_hand
OUT = "/home/claude/kits/out114/stage_bb"
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
def rel_of(f): return os.path.basename(f)[:-4].replace('__', '/') + '.stl'
def get(key): return [x for x in key_files('') if x.endswith(key + '.npz')][0]
side_out = {}
def put(f, d):
    d = dict(schemaVersion=1, part=os.path.splitext(os.path.basename(rel_of(f)))[0], **d)
    d.setdefault('sockets', [])
    side_out[rel_of(f)] = d
def sock(f, typ, M, note):
    stem = os.path.splitext(os.path.basename(rel_of(f)))[0]
    return dict(type=typ, name=f"{stem}_socket_{typ}", matrix=R(M), display_type="ARROWS", display_size=3.0, props={"tiow_from": note})
# ---------------------------------------------------------------- arms
ARM_KEYS = ['__Arms__', 'Chaplain__LArm', 'ChaplainRArm', 'RarmEmpty', 'Paragon Blade__LArm', 'Paragon Blade__RArm2', 'Rarm_TwoHanded']
HELD = ('LArm1', 'LArm2', 'LArm2_Bionic', 'LArm3', 'LArm4_ShoulderBolts', 'LArm4_ShoulderStuds', 'LArm1_Sh', 'LArm2_Sh', 'LArm2_Bionic_Sh')
arm_W = {}
for f in [x for x in key_files('BBoosty') if any(k in x for k in ARM_KEYS)]:
    short = os.path.basename(f)[:-4].split('__')[-1]
    side = 'L' if short.lower().startswith('larm') and 'RightVersion' not in short else 'R'
    V, F = load(f); d = shoulder_disc(V, F, side)
    if d is None: continue
    W = arm_world(d, side); arm_W[f] = (W, side, d)
# arms whose disc is hidden: the same arm with other trim (ICP), or the mirror of the left version
from align import icp
def via(f, g, mirror=False):
    V, F = load(f); G, FG = load(g)
    src = (G * ([-1, 1, 1] if mirror else 1)); rs = np.random.default_rng(0)
    src = src[rs.choice(len(src), 4000, replace=False)]
    best = None
    from align import rots
    for Rk in rots():
        M0 = np.eye(4); M0[:3, :3] = Rk; M0[:3, 3] = V.mean(0) - Rk @ src.mean(0)
        M, med, q = icp(src, V, M0, it=20)
        if best is None or med < best[1]: best = (M, med, q)
    M, med, q = icp(src, V, best[0], it=60)
    return M, med                      # (mirrored) g file -> f file
for f, (g, mir) in {get('Arms__LArm4_ShoulderBolts'): (get('Arms__LArm4_ShoulderStuds'), False),
                    get('Praetor with Paragon Blade__Praetor with Paragon Blade__LArm_ParagonBlade_Gear_ShoulderBolts_RightVersion'): (get('Praetor with Paragon Blade__Praetor with Paragon Blade__LArm_ParagonBlade_Gear_ShoulderBolts'), True),
                    get('Praetor with Paragon Blade__Praetor with Paragon Blade__LArm_ParagonBlade_Skull_ShoulderBolts_RightVersion'): (get('Praetor with Paragon Blade__Praetor with Paragon Blade__LArm_ParagonBlade_Skull_ShoulderBolts'), True)}.items():
    if g not in arm_W: continue
    M, med = via(f, g, mir)
    Wg, sg, dg = arm_W[g]
    if mir:   # right version = mirror image of the left arm: world = MX @ Wg @ MXfile, file map M: MX g -> f
        W = MX @ Wg @ MX @ np.linalg.inv(M); side = 'R'
    else:
        W = Wg @ np.linalg.inv(M); side = sg
    arm_W[f] = (W, side, dict(cc=W[:3, :3].T @ (S_H[:3, 3] if side == 'R' else (MX @ S_H)[:3, 3]) - W[:3, :3].T @ W[:3, 3], n=None, r=None, via=os.path.basename(g), med=med))
    print('via', os.path.basename(f)[-50:], '<-', os.path.basename(g)[-40:], 'med %.3f' % med)
for f, (W, side, d) in sorted(arm_W.items()):
    short = os.path.basename(f)[:-4].split('__')[-1]
    S = S_R if side == 'R' else S_L
    socks = []; notes = {"Shoulder": "BBoosty arms come in the model's own axes: the round flat shoulder face on the heresy shoulder point (Josh's HeresyArms_r, as Springles), square to the side, turned 180 deg (BBoosty front = -Y)"}
    if not short.startswith(HELD) and 'ParagonBlade' not in short:
        V, F = load(f); cup = cup_of(V, F, d['cc'] if d.get('n') is not None else None)
        if cup is not None:
            socks.append(sock(f, f"Hand {side}", hand_socket(cup, W), "BBoosty wrist socket: ball seat, Y into the arm, Z = torso forward (a little up)"))
            notes["Hand"] = "ball socket at the wrist (r %.2f)" % cup['r']
    put(f, dict(category="Arms", sockets=socks, fits={f"Shoulder {side}": R(np.linalg.inv(S) @ W)}, notes=notes))
print('arms', len(arm_W))
json.dump({k: v for k, v in side_out.items()}, open('/home/claude/kits/nc/bb_side_arms.json', 'w'))
