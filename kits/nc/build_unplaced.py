"""BBoosty / CyberBrush parts with no placement rule yet: a sidecar with just the type, so they go into the library in the
right type folder and import (and park on their socket where the type has one). Posed bodies and posed weapons left out (Josh)."""
import json, os, glob, re
P = '/home/claude/kits/nc/'
CAT = [  # (regex on the npz key, category)
    (r'BBoosty__Chaplain__ChaplainBody$|__PosedWeapon__|__Poses__', None),
    (r'IronFather__(Claw|Flamer|Melta)$', 'Servo Arms'),
    (r'__ServoArms__', 'Servo Arms'),
    (r'Backpacks__Backpack1_GearTrim_ParalClaw_Cables_Cam$', 'Backpacks'),
    (r'Backpacks__Backpackcam(Big)?$', 'Backpack Toppers'),
    (r'__SeparatedWeapon__|Two_Handed_Power_Sword_(Gear|Skull)$', 'Hand-less Weapons'),
    (r'Stuff__(Crack_Grenade|Frag_Grenade|MeltaBomb)$', 'Grenades'),
    (r'Stuff__(Grenade_Pouch|Holster_.*)$', 'Accessories'),
    (r'Stuff__(SergantShield|Shield)$', 'Shields'),
    (r'__BaseTopper$', 'Bases'),
    (r'Unsupported__Equipment \d$', 'Accessories'),
    (r'Space Bug Hunters Belt Decorations__', 'Accessories'),
    (r'Space Bug Hunters Cloaks__', 'Cloaks'),
    (r'Space Bug Hunters Loinclothes__', 'Accessories'),
    (r'Space Bug Hunters Shields__\d', 'Shields'),
    (r'__Free [^_]+$|__Space Bug 2 hand Sword \(5\)$|__Space Bug Hunter 2H Axe \(5\)$|Guns__Gun $|Guns__Gun \(Bayonet\)$', 'Hand-less Weapons'),
]
out = {}; left = []
for f in sorted(glob.glob(P + 'npz/*.npz')):
    k = os.path.basename(f)[:-4]
    if not k.startswith(('BBoosty', 'CyberBrush')): continue
    for rx, cat in CAT:
        if re.search(rx, k):
            if cat: out[k.replace('__', '/') + '.stl'] = dict(schemaVersion=1, part=k.split('__')[-1], category=cat, sockets=[], fits={},
                                                             notes={"type": "not placed yet: imports and parks on its socket (or lands at the cursor)"})
            break
    else:
        left.append(k)
json.dump(out, open(P + 'bbcb_unplaced.json', 'w'), indent=1)
from collections import Counter
print(len(out), Counter(d['category'] for d in out.values()))
print('no rule (placed elsewhere or skipped):', len(left))
