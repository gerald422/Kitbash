"""Sidecars for Mar Fil's Chaplain with Jump Pack (All Mar All the time\\ChaplainWithJumpPack (1)). The chest is the
Assault Marine torso (same joints); the four poses (A-D) are each exported in their own frame: the torso pose of each
comes from its arm pair's shoulder discs (0.01 mm), so the arms go on the shoulders as posed, the legs are seated like
Josh's AM legs, and the head, jump pack and belt bits (exported on the unposed torso) go where Mar Fil put them."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, collections
inv = np.linalg.inv
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
TOR = {s['type']: np.array(s['matrix']).reshape(4, 4) for s in P['AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/22-Torso-1.stl']['sockets']}
S_R, S_L, S_NECK, S_BACK, S_WAIST = (TOR[k] for k in ('Shoulder R', 'Shoulder L', 'Neck', 'Back', 'Waist'))
O = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
PO = json.load(open('/home/claude/kits/cj/pose.json'))
D = json.load(open('/home/claude/kits/cj/discs.json'))
WR = json.load(open('/home/claude/kits/cj/wrist2.json'))
HW = json.load(open('/home/claude/kits/cj/wrist.json'))['weapons']
ACC = json.load(open('/home/claude/kits/cj/acc.json'))
PADS = json.load(open('/home/claude/kits/cj/cj_pads.json'))
side_data = {}
def entry(rel, category=None):
    d = side_data.setdefault(rel, {'schemaVersion': 1, 'part': os.path.splitext(os.path.basename(rel))[0], 'sockets': [], 'fits': {}})
    if category: d['category'] = category
    return d
def flat(M): return [float(x) for x in np.asarray(M).reshape(-1)]
def add_socket(rel, tname, M, size=3.0, note=None, props=None, keep=False):
    d = entry(rel)
    if not keep: d['sockets'] = [s for s in d['sockets'] if s['type'] != tname]
    pr = dict(props or {});
    if note: pr['tiow_from'] = note
    d['sockets'].append({'type': tname, 'name': f"{d['part']}_socket_{tname}", 'matrix': flat(M), 'display_type': 'ARROWS', 'display_size': size, 'props': pr})
def add_fit(rel, tname, F): entry(rel)['fits'][tname] = flat(F)
rep = []
# chest
rel = O + 'Chest/Chest-Raw-STL/2-ChestChaplain.stl'; entry(rel, 'Chests')
for t, S in (('Shoulder R', S_R), ('Shoulder L', S_L), ('Neck', S_NECK), ('Back', S_BACK), ('Waist', S_WAIST)):
    add_socket(rel, t, S, note='Assault Marines torso joints (the chest matches at every joint)')
rep.append((rel, 'Chests', 'torso sockets'))
# head, jump pack, exhaust: exported on the unposed torso
rel = O + 'Head/Head-Raw-STL/1-Head.stl'; entry(rel, 'Heads')
# same seat as every other head: the AM helmet's neck ring (Josh's fit) matched onto this head (Mar Fil's export sits 4.5 deg off it)
from neckfit import neck_fit
Fn, mdn = neck_fit(rel); add_fit(rel, 'Neck', Fn); rep.append((rel, 'Heads', 'AM helmet neck seat (match %.3f)' % mdn))
rel = O + 'Jumppack/Jumppack-Raw-STL/11-Jumppack.stl'; entry(rel, 'Jump Packs'); add_fit(rel, 'Back', inv(S_BACK))
add_socket(rel, 'Back Top', np.eye(4), note='the exhaust, as exported'); rep.append((rel, 'Jump Packs', 'as exported on the chest, + Back Top'))
rel = O + 'Jumppack/Jumppack-Raw-STL/12-Exhaust.stl'; entry(rel, 'Backpack Toppers'); add_fit(rel, 'Back Top', np.eye(4)); rep.append((rel, 'Backpack Toppers', 'on the jump pack as exported'))
# legs + rocks
ROCK = {'A': '29-Rock-A', 'B': '28-Rock-B', 'C': '27-Rock-C', 'D': '30-Rock-D'}
for X, p in PO.items():
    rel = p['legs']; entry(rel, 'Legs'); add_socket(rel, 'Base', np.eye(4), note='legs file origin (its rock)')
    add_fit(rel, 'Waist', inv(S_WAIST) @ np.array(p['M_josh']))
    add_socket(rel, 'Hip R', p['hips']['Hip R'], note='hip, from ' + os.path.basename(p['ref']))
    for a, (t, M) in ACC['anchors'][X].items():      # Mar Fil's spots: Hip L holster, Belt Front badge, Belt Back book + grenade
        add_socket(rel, t, M, size=1.5, note="where Mar Fil put " + a, props={'tiow_holds': a}, keep=True)
    rep.append((rel, 'Legs', "seated like Josh's AM legs, + belt anchors"))
    r = O + 'Rocks/Rocks-Raw-STL/' + ROCK[X] + '.stl'; entry(r, 'Bases'); add_fit(r, 'Base', np.eye(4)); rep.append((r, 'Bases', 'under the legs, as exported'))
# arms: torso pose of the pose they belong to, shoulder disc centre on the joint; Hand socket from the wrist rule
ARMS = {'A': ('13-Arm-Right-A', '17-Arm-Left-A'), 'B': ('14-Arm-Right-B', '18-Arm-Left-B'), 'C': ('15-Arm-Right-C', '19-Arm-Left-C'), 'D': ('16-Arm-Right-D', '20-Arm-Left-D')}
for X, (r, l) in ARMS.items():
    Pi = inv(np.array(PO[X]['P']))
    for name, sd, S in ((r, 'R', S_R), (l, 'L', S_L)):
        rel = O + 'Arms/Arms-Raw-STL/' + name + '.stl'; c = np.array(D[rel][0]['c'])
        A = Pi.copy(); A[:3, 3] = S[:3, 3] - Pi[:3, :3] @ c          # arm file -> torso, disc centre on the joint
        entry(rel, 'Arms'); add_fit(rel, 'Shoulder ' + sd, inv(S) @ A)
        add_socket(rel, 'Hand ' + sd, np.array(WR[rel]), note='wrist rule (outermost round face)')
        rep.append((rel, 'Arms', 'posed torso of its pair, disc on the joint'))
# weapons with a hand: the hand rule
for w, cat, sd in (('21-AbsolvorPistol', 'Pistols', 'L'), ('22-Crozius', 'Melee', 'R')):
    rel = O + 'Weapons/Weapons-Raw-STL/' + w + '.stl'; h = HW[rel + '|' + sd]
    entry(rel, cat); add_fit(rel, 'Hand ' + sd, inv(np.array(h['M']))); rep.append((rel, cat, 'hand rule (fist %.2f)' % h['med']))
# belt bits
for a, cat in (('23-Book', 'Accessories'), ('24-Badge', 'Accessories'), ('25-Holster', 'Accessories'), ('26-Grenade', 'Grenades')):
    rel = O + 'Accesories/Accesories-Raw-STL/' + a + '.stl'; F = inv(np.array(ACC['K'][a])); entry(rel, cat)
    for t in ('Hip R', 'Hip L', 'Belt Front', 'Belt Back'): add_fit(rel, t, F)
    rep.append((rel, cat, 'back on the belt, Y up (any belt anchor)'))
# pads
for rel, v in PADS.items():
    rel = rel[len('All Mar All the time/'):]
    entry(rel, 'Knee Pads' if v['type'].startswith('Shin') else 'Shoulder Pads'); add_fit(rel, v['type'], np.array(v['fit']))
    rep.append((rel, side_data[rel]['category'], f"{v['type']} (match {v['median']:.2f})"))
cnt = collections.Counter((r[1], r[2]) for r in rep)
for k, n in sorted(cnt.items()): print('%3d  %-18s %s' % (n, k[0], k[1]))
json.dump({'side': side_data}, open('/home/claude/kits/cj/cj_partial.json', 'w'))
files = [os.path.relpath(os.path.join(dp, f), geo.U) for dp, dn, fn in os.walk(geo.U + "ChaplainWithJumpPack (1)") for f in fn if f.endswith('.stl')]
print(len(side_data), 'sidecars of', len(files), 'files; missing:', sorted(set(files) - set(side_data)))
import fix_belts; fix_belts.fix('/home/claude/kits/cj/cj_partial.json', '')   # belt anchors by rule, same frame on every kit's legs
