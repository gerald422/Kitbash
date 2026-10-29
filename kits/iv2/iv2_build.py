"""Sidecars for Mar Fil's Intercessors V2 (D:\\new cults\\Intercessors-V2): same torso joints as the Assault Marines /
Vet kits (the kit frame is shared), legs seated like Josh's AM legs, separate hands with a Grip for the hand-less
weapons, hand-held parts on the kit's wrist frames, arm pieces on their shoulder ball."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, re, collections
from scipy.spatial import cKDTree
inv = np.linalg.inv; MX = np.diag([-1.0, 1, 1, 1])
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
TOR = {s['type']: np.array(s['matrix']).reshape(4, 4) for s in P['AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/22-Torso-1.stl']['sockets']}
S_R, S_L, S_NECK, S_BACK, S_WAIST = (TOR[k] for k in ('Shoulder R', 'Shoulder L', 'Neck', 'Back', 'Waist'))
J_ARM = np.array([5.568, 0.202, 31.949])
ARM_R = geo.M4(np.eye(3), -J_ARM); ARM_L = geo.M4(np.eye(3), -J_ARM * [-1, 1, 1])
S_CABLE = geo.M4(np.eye(3), np.array([7.0, 1.0, 22.0]))           # same cable mount as the Vet kit (kit frame)
AMH = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/Helmet-Heads/1-Helmet-1.stl'
F_AMH = np.array(P[AMH]['fits']['Neck']).reshape(4, 4)
# wrist frames (hand rule, kit-wide): the separate hands, the melee and pistol pieces share one wrist; the hand-held
# bolters another (their own hand, wrist at the stock end)
WkR = geo.M4(np.eye(3), np.array([-1.13, 2.77, 1.20])); WkL = MX @ WkR @ MX
WbR = geo.M4(np.diag([-1.0, -1, 1]), np.array([0.82, -8.43, -2.94]))
WbL = geo.M4(np.diag([-1.0, -1, 1]), np.array([-0.845, -8.42, -2.855]))
RZ90 = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])   # hand-less bolter -> held bolter
H = json.load(open('/home/claude/kits/iv2/hands.json'))
W282 = {'R': np.array(H['Hands-Raw/282-Hand-10-R.stl']['M']), 'L': np.array(H['Hands-Raw/Hand-Left/282-Hand-10-L.stl']['M'])}
SEAT = {k[3:]: v for k, v in json.load(open('/home/claude/kits/iv2/legs_seat.json')).items()}    # '../X' -> 'X'
DF = json.load(open('/home/claude/kits/iv2/disc_fits.json'))      # shoulder disc of each arm piece -> on the joint, flush
PADS = json.load(open('/home/claude/kits/iv2/iv2_pads.json'))
KIT = 'Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/'
files = [KIT + l.split('\t')[1].strip()[len('./Intercessors-V2/Intercessors-Bits/RawSTL/'):] for l in open('/home/claude/kits/iv2/data/iv2.tsv') if l.strip()]
BB = json.load(open('/home/claude/kits/iv2/data/cls.json'))

side_data = {}
def entry(rel, category=None):
    d = side_data.setdefault(rel, {'schemaVersion': 1, 'part': os.path.splitext(os.path.basename(rel))[0], 'sockets': [], 'fits': {}})
    if category: d['category'] = category
    return d
def flat(M): return [float(x) for x in np.asarray(M).reshape(-1)]
def add_socket(rel, tname, M, size=3.0, note=None):
    d = entry(rel); d['sockets'] = [s for s in d['sockets'] if s['type'] != tname]
    d['sockets'].append({'type': tname, 'name': f"{d['part']}_socket_{tname}", 'matrix': flat(M), 'display_type': 'ARROWS', 'display_size': size, 'props': {'tiow_from': note} if note else {}})
def add_fit(rel, tname, F): entry(rel)['fits'][tname] = flat(F)

def neck_fit(helmet_rel):
    V, T = geo.load(AMH); S = geo.surf(V, T, 200000)
    W, U = geo.load(helmet_rel); Q = geo.surf(W, U, 200000); tree = cKDTree(Q)
    full = S[np.random.default_rng(1).choice(len(S), 3000, replace=False)]
    neck = inv(F_AMH)[:3, 3]; reg = S[np.linalg.norm(S - neck, axis=1) < 4.0]
    best = None
    for a in (0, 90, 180, 270):
        c, s_ = np.cos(np.radians(a)), np.sin(np.radians(a)); R0 = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
        R, t, d = geo.icp(full, tree, Q, R0, Q.mean(0) - R0 @ S.mean(0), 40); R, t, d = geo.icp(reg, tree, Q, R, t, 30)
        if best is None or np.median(d) < best[0]: best = (float(np.median(d)), geo.M4(R, t))
    return F_AMH @ inv(best[1]), best[0]

TWO_H = {179, 180, 182, 183, 185, 186, 195, 196, 197, 198, 199, 200, 207, 209, 211}
CABLE = {181, 184, 187, 190, 192, 194, 206, 208, 210, 212}
R_ARM = {188, 189, 191, 193, 201, 203, 205}
L_ARM = {202, 204}
LAUNCHER = {213, 214, 215, 216, 217, 218}
rep = []
def arm_fit(rel, side):
    g = DF.get(rel)
    if g is None or g['side'] != side: return None
    return np.array(g['fit'])
for rel in files:
    sub = rel[len(KIT):]; f = os.path.basename(rel); low = sub.lower()
    num = int(re.match(r'(\d+)', f).group(1)) if re.match(r'(\d+)', f) else None
    left = '/hand-left/' in low or '-left/' in low or f.endswith('-L.stl')
    sd = 'L' if left else 'R'
    if low.startswith('chest-raw/'):
        entry(rel, 'Chests')
        for t, S in (('Shoulder R', S_R), ('Shoulder L', S_L), ('Neck', S_NECK), ('Back', S_BACK), ('Waist', S_WAIST)):
            add_socket(rel, t, S, note='Assault Marines torso joints (kit frame shared)')
        rep.append((rel, 'Chests', 'torso sockets'))
    elif low.startswith('legs-raw/'):
        st = SEAT[rel]; entry(rel, 'Legs'); add_socket(rel, 'Base', np.eye(4), note='legs file origin')
        add_fit(rel, 'Waist', inv(S_WAIST) @ np.array(st['M']))
        for h, M in st['hips'].items(): add_socket(rel, h, M, note='hip, from ' + os.path.basename(st['ref']))
        rep.append((rel, 'Legs', 'seated like Josh\'s AM legs'))
    elif low.startswith('arms-raw/'):
        entry(rel, 'Arms'); add_fit(rel, 'Shoulder ' + sd, ARM_L if left else ARM_R); rep.append((rel, 'Arms', 'joint at the inner face'))
    elif low.startswith('hands-raw/'):
        if num == 282:
            entry(rel, 'Shields'); add_fit(rel, 'Hand ' + sd, inv(W282[sd])); rep.append((rel, 'Shields', 'hand + shield, hand rule'))
        else:
            entry(rel, 'Hands'); add_fit(rel, 'Hand ' + sd, inv(WkL if left else WkR))
            add_socket(rel, 'Grip ' + sd, WkL if left else WkR, size=2.0, note='kit wrist frame: Mar Fil\'s hand-less weapons fit here')
            rep.append((rel, 'Hands', 'kit wrist + Grip'))
    elif low.startswith('melee-handed-raw/'):
        entry(rel, 'Melee'); add_fit(rel, 'Hand ' + sd, inv(WkL if left else WkR)); rep.append((rel, 'Melee', 'kit wrist'))
    elif low.startswith('weapons-raw/'):
        entry(rel, 'Pistols'); add_fit(rel, 'Hand ' + sd, inv(WkL if left else WkR)); rep.append((rel, 'Pistols', 'kit wrist'))
    elif low.startswith('melee-nohand/') or (low.startswith('weapons-nohand-raw/') and 'bolter' not in low):
        entry(rel, 'Hand-less Weapons'); add_fit(rel, 'Grip R', inv(WkR)); add_fit(rel, 'Grip L', inv(WkL)); rep.append((rel, 'Hand-less Weapons', 'grip as in the kit'))
    elif low.startswith('weapons-nohand-raw/'):
        entry(rel, 'Hand-less Weapons'); add_fit(rel, 'Grip R', inv(WbR) @ RZ90); add_fit(rel, 'Grip L', inv(WbL) @ RZ90); rep.append((rel, 'Hand-less Weapons', 'bolter grip as in the held bolters'))
    elif low.startswith('bolter-individual-raw/'):
        if num >= 144:
            entry(rel, 'Pistols'); add_fit(rel, 'Hand ' + sd, inv(WbL if left else WbR)); rep.append((rel, 'Pistols', 'held bolter, its own wrist'))
        else:
            F = arm_fit(rel, sd)
            if F is None: rep.append((rel, '-', 'arm piece without a shoulder match')); continue
            entry(rel, 'Arms'); add_fit(rel, 'Shoulder ' + sd, F); rep.append((rel, 'Arms', 'arm with bolter, shoulder disc (pairs rigid)'))
    elif low.startswith('bolter-dual-raw/'):
        entry(rel, 'Two-Handed Guns'); add_fit(rel, 'Shoulder R', inv(S_R)); rep.append((rel, 'Two-Handed Guns', 'kit position'))
    elif low.startswith(('desolator-raw/', 'plasmaincinerator-raw/', 'pyreblaster-raw/')):
        lside = '-left/' in low
        if num in LAUNCHER: rep.append((rel, '-', 'launcher bit, not placed')); continue
        if num in CABLE:
            entry(rel, 'Heavy Weapon Cables'); add_fit(rel, 'Cable', inv(S_CABLE)); rep.append((rel, 'Heavy Weapon Cables', 'kit position'))
        elif num in TWO_H and not lside:
            entry(rel, 'Heavy Weapons'); add_fit(rel, 'Shoulder R', inv(S_R)); add_socket(rel, 'Cable', S_CABLE, note='cable mount (kit frame)')
            rep.append((rel, 'Heavy Weapons', 'kit position'))
        elif num in R_ARM and not lside:
            F = arm_fit(rel, 'R')
            if F is None: rep.append((rel, '-', 'arm piece without a shoulder match')); continue
            entry(rel, 'Arms'); add_fit(rel, 'Shoulder R', F); add_socket(rel, 'Cable', S_CABLE, note='cable mount (kit frame)')
            rep.append((rel, 'Arms', 'arm with heavy weapon, shoulder disc'))
        elif num in L_ARM or lside:
            F = arm_fit(rel, 'L')
            if F is None: rep.append((rel, '-', 'arm piece without a shoulder match')); continue
            entry(rel, 'Arms'); add_fit(rel, 'Shoulder L', F); rep.append((rel, 'Arms', 'left arm for a heavy weapon, shoulder disc'))
        else: rep.append((rel, '-', 'not handled'))
    elif low.startswith('helmets-heads-raw/'):
        entry(rel, 'Heads'); rep.append((rel, 'Heads', 'kit neck fit'))
    elif low.startswith('backpacks-raw/'):
        entry(rel, 'Backpacks'); add_fit(rel, 'Back', inv(S_BACK)); rep.append((rel, 'Backpacks', 'kit position'))
    elif low.startswith(('shinpad-raw/', 'shoulderpad-raw/')):
        v = PADS.get(rel)
        if v is None: rep.append((rel, '-', 'pad not matched')); continue
        entry(rel, 'Knee Pads' if v['type'].startswith('Shin') else 'Shoulder Pads'); add_fit(rel, v['type'], np.array(v['fit']))
        rep.append((rel, side_data[rel]['category'], f"{v['type']} (match {v['median']:.2f})"))
    elif low.startswith('rocks-raw/'):
        entry(rel, 'Bases'); add_fit(rel, 'Base', np.eye(4)); rep.append((rel, 'Bases', 'under the legs, as exported'))
    else:
        rep.append((rel, '-', 'not handled'))
F, md = neck_fit('../' + KIT + 'Helmets-Heads-Raw/1-Helmet-1.stl')
for rel in [r for r in side_data if r.startswith(KIT + 'Helmets-Heads-Raw/')]: add_fit(rel, 'Neck', F)
print('Neck fit from 1-Helmet-1: AM helmet match %.3f' % md)
cnt = collections.Counter((r[1], r[2]) for r in rep)
for k, n in sorted(cnt.items()): print('%3d  %-20s %s' % (n, k[0], k[1]))
json.dump({'side': side_data}, open('/home/claude/kits/iv2/iv2_partial.json', 'w'))
print(len(side_data), 'sidecars of', len(files), 'files')
import fix_belts; fix_belts.fix('/home/claude/kits/iv2/iv2_partial.json', '../')   # belt anchors by rule, same frame on every kit's legs
