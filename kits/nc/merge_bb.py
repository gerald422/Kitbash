"""All BBoosty sidecars -> stage dir (D:\\new cults relative paths) + test library."""
import json, os, sys, numpy as np
sys.path.insert(0, '/home/claude/kits/nc')
from geo import *; from bases import base_frame
import mklib
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
STAGE = "/home/claude/kits/out114/stage_bb"
sides = {}
for f in ['bb_side_arms.json', 'bb_side_hands.json', 'bb_side_heads_packs.json', 'bb_side_2h.json', 'bb_side_more.json']:
    p = '/home/claude/kits/nc/' + f
    if os.path.exists(p):
        d = json.load(open(p)); sides.update(d.get('side', d) if 'side' in d else d)
for rel, d in sides.items():
    if d.get('category') == 'Arms':
        d['noPad'] = True
        d.setdefault('notes', {})['Pad'] = "no pauldron anchor yet (BBoosty pads to come)"
# bases
for k in ['Chaplain__Base', 'IronFather__Base', 'Praetor with Paragon Blade__Praetor with Paragon Blade__Base', 'Praetor with Paragon Blade__Praetor with Paragon Blade__Textured Base']:
    f = [x for x in key_files('BBoosty') if x.endswith(k + '.npz')][0]; V, F = load(f)
    M, r, top = base_frame(V, F); rel = os.path.basename(f)[:-4].replace('__', '/') + '.stl'
    sides[rel] = dict(schemaVersion=1, part=os.path.splitext(os.path.basename(rel))[0], category="Bases", sockets=[], fits={"Base": R(np.linalg.inv(M))},
                      notes={"Base": "round base rule: centre of the disc at the top, Z up from the bottom face; the legs stand on it"})
for rel, d in sides.items():
    p = os.path.join(STAGE, rel[:-4] + '.sockets.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, 'w'), indent=1)
mklib.build(sides)
from collections import Counter
print(len(sides), Counter(d['category'] for d in sides.values()))
