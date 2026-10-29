"""All BBoosty + CyberBrush sidecars -> stage dirs (D:\\new cults relative) + test library."""
import json, os, sys, numpy as np
sys.path.insert(0, '/home/claude/kits/nc')
from geo import *; from bases import base_frame
import mklib
R = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
STAGE = "/home/claude/kits/out114/stage"
P = '/home/claude/kits/nc/'
def ld(f):
    if not os.path.exists(P + f): print('missing', f); return {}
    d = json.load(open(P + f)); return d['side'] if 'side' in d and isinstance(d['side'], dict) else d
sides = {}
for f in ['bb_side_arms.json', 'bb_side_hands.json', 'bb_side_hands2.json', 'bb_side_heads_packs.json', 'bb_side_2h.json', 'bb_side_pads.json',
          'cb_side_arms.json', 'cb_side_body.json', 'cb_side_packs.json', 'cb_side_pads.json', 'cb_side_forearms.json', 'cb_side_arms2.json']:
    sides.update(ld(f))
# not arms: the CyberBrush loose guns
for k in [k for k in sides if k.endswith(('Guns/Gun .stl', 'Guns/Gun (Bayonet).stl'))]: del sides[k]
# parts with no placement rule yet: type only (never over a placed part)
for rel, d in ld('bbcb_unplaced.json').items():
    if rel not in sides: sides[rel] = d
anchors = {}
for f in ['bb_pad_anchors.json', 'cb_pad_anchors.json', 'cb_pad_anchors2.json']:
    anchors.update(ld(f))
for rel, d in sides.items():
    if d.get('category') != 'Arms': continue
    side = 'R' if any(k.startswith('Shoulder R') for k in d['fits']) else 'L'
    stem = os.path.basename(rel)[:-4]
    integrated = 'Shoulder' in stem             # BBoosty arms with their pad built in
    d['sockets'] = [s for s in d.get('sockets', []) if not s['type'].startswith('Pad ')]
    if rel in anchors and not integrated:
        d['sockets'].append(dict(type=f"Pad {side}", name=f"{stem}_socket_Pad {side}", matrix=anchors[rel], display_type="ARROWS", display_size=3.0,
                                 props={"tiow_anchor": "dome", "tiow_from": "Josh's 62 on the Springles heresy arm (actual.blend), moved so its inner shell centres on this arm's shoulder dome"}))
        d['noPad'] = False; d.setdefault('notes', {})['Pad'] = "Pad anchor on the shoulder dome: Mar Fil pads sit as on the heresy arms, this maker's pads with their shell on the dome"
    else:
        d['noPad'] = True; d.setdefault('notes', {})['Pad'] = "pad built in" if integrated else "no shoulder dome found: no pauldron anchor"
# arms whose hand is part of them (holding a weapon, a grip or a claw): no wrist socket wanted
for rel, d in sides.items():
    if d.get('category') == 'Arms' and not any(s['type'].startswith('Hand') for s in d.get('sockets', [])):
        d['noHand'] = True; d.setdefault('notes', {})['Hand'] = "hand built in (holding its weapon, a shield grip or a claw): no wrist socket"
# bases
for k in ['Chaplain__Base', 'IronFather__Base', 'Praetor with Paragon Blade__Praetor with Paragon Blade__Base', 'Praetor with Paragon Blade__Praetor with Paragon Blade__Textured Base']:
    f = P + 'npz/BBoosty__' + k + '.npz'; V, F = load(f)
    M, r, top = base_frame(V, F); rel = 'BBoosty/' + k.replace('__', '/') + '.stl'
    sides[rel] = dict(schemaVersion=1, part=os.path.basename(rel)[:-4], category="Bases", sockets=[], fits={"Base": R(np.linalg.inv(M))},
                      notes={"Base": "round base rule: centre of the disc at the top, Z up from the bottom face; the legs stand on it"})
import shutil
if os.path.isdir(STAGE): shutil.rmtree(STAGE)
for rel, d in sides.items():
    p = os.path.join(STAGE, rel[:-4] + '.sockets.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, 'w'), indent=1)
mklib.build(sides)
from collections import Counter
for cr in ('BBoosty', 'CyberBrush'):
    print(cr, sum(1 for r in sides if r.startswith(cr)), Counter(d['category'] for r, d in sides.items() if r.startswith(cr)))
print('arms with Pad anchor', sum(1 for d in sides.values() if d.get('category') == 'Arms' and any(s['type'].startswith('Pad') for s in d['sockets'])))
