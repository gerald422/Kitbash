"""BBoosty phase 1c: heads (neck ball in the Mar Fil neck cup, model axes) and backpacks (Josh's Backpack2 placement)."""
import numpy as np, json, os
from geo import *; from bbrules import *
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
def rel_of(f): return os.path.basename(f)[:-4].replace('__', '/') + '.stl'
def get(key): return [x for x in key_files('') if x.endswith(key + '.npz')][0]
P = 'Praetor with Paragon Blade__Praetor with Paragon Blade__'; MM = 'Medusas Mortals__Medusas Mortals__'
side_out = {}
def put(f, d):
    d = dict(schemaVersion=1, part=os.path.splitext(os.path.basename(rel_of(f)))[0], **d); d.setdefault('sockets', []); side_out[rel_of(f)] = d
NECK_CUP = np.array([0.0, 1.14, 35.22])          # Mar Fil 23-Torso-2 neck cup centre (r 2.67)
for key in ['Chaplain__Head', 'Chaplain__Head_Wireless', 'Chaplain__Helmet', 'Consul__Head', 'Consul__Head_Wireless', 'Consul__Helmet', 'IronFather__Head']:
    f = get(key); V, F = load(f)
    b = balls(V, F, 2.2, 3.1, minc=0.3, k=3)
    b = min(b, key=lambda o: o['c'][2])          # the lowest ball is the neck
    W = T(NECK_CUP) @ RZ180 @ T(-b['c'])
    put(f, dict(category="Heads", fits={"Neck": R(np.linalg.inv(S_NECK) @ W)},
                notes={"Neck": "BBoosty neck ball (r %.2f) centred in the Mar Fil neck cup, the model's own axes turned 180 deg (BBoosty front = -Y)" % b['r']}))
    print('%-26s ball r %.2f c %s' % (key, b['r'], np.round(b['c'], 2)))
bp2 = get(MM + 'Backpacks__Backpack2'); V2, F2 = load(bp2)
W2 = S_BACK @ np.array(json.load(open('/home/claude/kits/nc/bb_back_fit.json'))['Back'])
def main_front(V, F):
    fl = flats(V, F, [0, -1, 0], cos=0.98, min_area=1.0); return fl[0] if fl else None
A2, c2, n2, g2 = main_front(V2, F2)
packs = [x for x in key_files('BBoosty') if '__Backpacks__' in x and 'cam' not in os.path.basename(x).lower()] + \
        [get(k) for k in ['Chaplain__Backpack', 'Chaplain__Backpack_Interrrior', 'Consul__Backpack', 'Consul__Backpack_Interrrior', 'IronFather__Backpack', P + 'Backpack', 'ServoArms__Backpack_for_servoarm']]
for f in packs:
    V, F = load(f); A, c, n, g = main_front(V, F)
    if abs(A - A2) < 3:          # the Medusa's Mortals pack body (and the Praetor's): same front plate
        off = c2 - c; how = "same pack body as Backpack2 (front plate matched)"
    else:                        # another pack: centred, front face on Backpack2's, bottom level
        lo, hi = V.min(0), V.max(0); lo2, hi2 = V2.min(0), V2.max(0)
        off = np.array([(lo2[0] + hi2[0]) / 2 - (lo[0] + hi[0]) / 2, c2[1] - c[1], lo2[2] - lo[2]]); how = "centred, front face and bottom level with Backpack2"
    W = W2 @ T(off)
    put(f, dict(category="Backpacks", fits={"Back": R(np.linalg.inv(S_BACK) @ W)},
                notes={"Back": "Josh's Backpack2 on 23-Torso-2 (actual.blend); " + how}))
    print('%-50s A %.1f off %s %s' % (os.path.basename(f)[-50:], A, np.round(off, 2), how[:30]))
json.dump(side_out, open('/home/claude/kits/nc/bb_side_heads_packs.json', 'w'))
