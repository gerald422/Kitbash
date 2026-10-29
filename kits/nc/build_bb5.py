"""BBoosty phase 1b: hands, with-hand weapons, two-handed swords, heads, backpacks."""
import numpy as np, json, os
from geo import *; from bbrules import *; from handfind import find_hand
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
def rel_of(f): return os.path.basename(f)[:-4].replace('__', '/') + '.stl'
def get(key): return [x for x in key_files('') if x.endswith(key + '.npz')][0]
P = 'Praetor with Paragon Blade__Praetor with Paragon Blade__'; MM = 'Medusas Mortals__Medusas Mortals__'
side_out = {}
def put(f, d):
    d = dict(schemaVersion=1, part=os.path.splitext(os.path.basename(rel_of(f)))[0], **d); d.setdefault('sockets', []); side_out[rel_of(f)] = d
def hand_frame(c, r, a, zhint):
    """Springles dome convention: origin 0.55 short of the ball's tip, Y = a (toward the arm)"""
    return frame_YZ(c + (r - 0.55) * a, a, zhint)
def far_dir(V, c, a, rmin=4.0):
    d = V - c; L = np.linalg.norm(d, axis=1); m = L > rmin
    if m.sum() < 50: return None
    v = (d[m] * (L[m] ** 2)[:, None]).sum(0); v -= (v @ a) * a; return v / np.linalg.norm(v)
# --- hand templates (ball + axis)
ONLY_WH = True
TPL = {}
for t in [MM + 'Stuff__Hand_Fist', MM + 'Stuff__Bionic_Hand_Fist', 'Chaplain__Hand', 'Chaplain__HandBionic']:
    V, F = load(get(t)); b = balls(V, F, 0.95, 1.45, minc=0.35, k=1)[0]
    a = -b['free']                      # from the ball's free side back into the hand ... the arm is on the free side
    TPL[t] = dict(V=V, c=b['c'], r=b['r'], free=b['free'])
# ---------------------------------------------------------------- bare hands
for key in [] if ONLY_WH else [MM + 'Stuff__Hand_Fist', MM + 'Stuff__Hand_Idle', MM + 'Stuff__Hand_Pointing', MM + 'Stuff__BionicHand_Idle', MM + 'Stuff__Bionic_Hand_Fist',
            MM + 'Stuff__Bionic_Hand_Pointing', 'Chaplain__Hand', 'Chaplain__HandBionic', P + 'Hand_Fist']:
    f = get(key); V, F = load(f); b = balls(V, F, 0.95, 1.45, minc=0.35, k=1)[0]
    a = b['free']                        # the arm is where the ball's free side faces
    H = hand_frame(b['c'], b['r'], a, np.array([0, 0, 1.0]))
    fit = R(np.linalg.inv(H))
    put(f, dict(category="Hands", fits={"Hand R": fit, "Hand L": fit},
                notes={"Hand": "BBoosty wrist ball (r %.2f) seated in the wrist socket; back of the hand (file +Z) to the torso's up+forward" % b['r']}))
# ---------------------------------------------------------------- with-hand weapons: find the hand sculpt in it
WH = {P + 'Two_Handed_Power_Sword_Gear_AngleGrip': 'Melee', P + 'Two_Handed_Power_Sword_Gear_BionicAngleGrip': 'Melee', P + 'Two_Handed_Power_Sword_Gear_BionicHand': 'Melee',
      P + 'Two_Handed_Power_Sword_Skull_AngleGrip': 'Melee', P + 'Two_Handed_Power_Sword_Skull_BionicAngleGrip': 'Melee', P + 'Two_Handed_Power_Sword_Skull_BionicHand': 'Melee',
      MM + 'Stuff__LHand_Bionic_SergantShield': 'Shields'}
WH0 = {'Consul__PowerAxe': 'Melee', 'Consul__PowerGlave': 'Melee', 'Consul__ThunderHammer': 'Melee', 'Chaplain__CroziusArcanum': 'Melee',
      'IronFather__PowerAxe': 'Melee', 'Chaplain__PlasmaPistol': 'Pistols', 'IronFather__BoltPistol': 'Pistols'}
found = {}
for key, cat in WH.items():
    f = get(key); V, F = load(f); best = None
    for t, T_ in TPL.items():
        M, med, q9 = find_hand(T_['V'], T_['c'], V, F, nrot=40)
        if best is None or q9 < best[2]: best = (t, M, q9, med)
    t, M, q9, med = best; T_ = TPL[t]
    c = M[:3, :3] @ T_['c'] + M[:3, 3]; a = M[:3, :3] @ T_['free']
    z = far_dir(V, c, a) if far_dir(V, c, a) is not None else np.array([0, 0, 1.0])
    H = hand_frame(c, T_['r'], a, z); fit = R(np.linalg.inv(H))
    found[key] = dict(t=t, q9=q9, med=med, c=c.tolist())
    put(f, dict(category=cat, fits={"Hand R": fit, "Hand L": fit},
                notes={"Hand": f"the hand in it matches BBoosty {t.split('__')[-1]} (q90 {q9:.2f} mm): its wrist ball in the wrist socket, the weapon's far end to the torso's up+forward"}))
    print('%-28s %-28s q90 %.2f med %.2f ball %s' % (key, t.split('__')[-1], q9, med, np.round(c, 1)))
json.dump({'side': side_out, 'found': found}, open('/home/claude/kits/nc/bb_side_hands2.json', 'w'))
