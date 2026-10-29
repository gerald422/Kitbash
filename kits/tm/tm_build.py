"""Sidecars for Mar Fil's Techmarine (All Mar All the time\\Techmarine (2)). Chest = the AM torso sockets; legs seated like
Josh's AM legs; arms exported on a turned torso per set (the turn from each set's two shoulder faces), so each goes on
the shoulder as posed; backpack with Servo Arm (the shoulder ball's seat from Mar Fil's build file), Mechadendrite and
Back Top (forge guns) sockets; arm cables on their arm; the separate hand and the hand-held parts by the hand rule."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, re, glob, collections
from scipy.spatial import cKDTree
from neckfit import neck_fit
inv = np.linalg.inv; MX = np.diag([-1.0, 1, 1, 1])
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
TOR = {s['type']: np.array(s['matrix']).reshape(4, 4) for s in P['AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/22-Torso-1.stl']['sockets']}
S_R, S_L, S_NECK, S_BACK, S_WAIST = (TOR[k] for k in ('Shoulder R', 'Shoulder L', 'Neck', 'Back', 'Waist'))
O = "Techmarine (2)/Techmarine/"
SEAT = json.load(open('/home/claude/kits/tm/legs_seat.json'))
POSE = json.load(open('/home/claude/kits/tm/pose.json'))
RU = json.load(open('/home/claude/kits/tm/rules.json'))
BALLS = json.load(open('/home/claude/kits/tm/balls.json')); SEATB = np.array(json.load(open('/home/claude/kits/tm/servo_seat.json'))['seat'])
PADS = json.load(open('/home/claude/kits/tm/tm_pads.json'))
WR = json.load(open('/home/claude/kits/tm/wrists.json'))        # left wrists: the rule at 20 % roundness (theirs stray 15-18 %)
side_data = {}
def entry(rel, category=None):
    d = side_data.setdefault(rel, {'schemaVersion': 1, 'part': os.path.splitext(os.path.basename(rel))[0], 'sockets': [], 'fits': {}})
    if category: d['category'] = category
    return d
def flat(M): return [float(x) for x in np.asarray(M).reshape(-1)]
def add_socket(rel, tname, M, size=3.0, note=None, props=None, keep=False):
    d = entry(rel)
    if not keep: d['sockets'] = [s for s in d['sockets'] if s['type'] != tname]
    pr = dict(props or {})
    if note: pr['tiow_from'] = note
    d['sockets'].append({'type': tname, 'name': f"{d['part']}_socket_{tname}", 'matrix': flat(M), 'display_type': 'ARROWS', 'display_size': size, 'props': pr})
def add_fit(rel, tname, F): entry(rel)['fits'][tname] = flat(F)
def T(v): M = np.eye(4); M[:3, 3] = v; return M
def placed(Pk, c, S):
    """arm file -> torso for an arm exported on torso pose Pk, its shoulder disc centre c put on the socket S"""
    A = inv(np.array(Pk)); A[:3, 3] = S[:3, 3] - A[:3, :3] @ np.asarray(c); return A
rep = []
files = sorted(os.path.relpath(f, geo.U) for f in glob.glob(geo.U + O + '*/*Raw-STL/*.stl'))
SET_OF = {'12': ('a', 'L'), '14': ('a', 'L'), '18': ('a', 'R'), '16': ('b', 'L'), '19': ('b', 'R')}
for rel in files:
    b = os.path.basename(rel); num = b.split('-')[0]; folder = rel.split('/')[2]
    if folder == 'Chest':
        entry(rel, 'Chests')
        for t, S in (('Shoulder R', S_R), ('Shoulder L', S_L), ('Neck', S_NECK), ('Back', S_BACK), ('Waist', S_WAIST)):
            add_socket(rel, t, S, note='Assault Marines torso joints (the Techmarine chest matches: waist/shoulders/neck 0.03 mm, back 2 deg)')
        rep.append((rel, 'Chests', 'torso sockets'))
    elif folder == 'Helmet':
        F, md = neck_fit(rel); entry(rel, 'Heads'); add_fit(rel, 'Neck', F); rep.append((rel, 'Heads', 'AM helmet neck seat (%.3f)' % md))
    elif folder == 'Legs':
        st = SEAT[rel]; entry(rel, 'Legs'); add_fit(rel, 'Waist', inv(S_WAIST) @ np.array(st['M']))
        add_socket(rel, 'Base', np.eye(4), note='legs file origin (feet on z = 0)')
        rep.append((rel, 'Legs', "seated like Josh's AM legs"))
    elif folder == 'Arms':
        if 'Cable' in b:
            entry(rel, 'Cables'); add_fit(rel, 'Cable', np.eye(4)); rep.append((rel, 'Cables', 'on its arm, as exported'))
            continue
        k, sd = SET_OF[num]; S = S_R if sd == 'R' else S_L
        c = POSE['14']['cL'] if num == '14' else POSE[k]['c' + sd]
        A = placed(POSE[k]['P'], c, S)
        entry(rel, 'Arms'); add_fit(rel, 'Shoulder ' + sd, inv(S) @ A)
        if num in ('12', '14', '16'): add_socket(rel, 'Cable', np.eye(4), size=2.0, note='its cable, as exported')
        # bionic wrists: the rule's roll (from forearm armour) doesn't hold; the roll of the hand Mar Fil exported on it
        # (hand 38 on 12, carried to 14/16 - same wrist sculpt, 0.016; the cog axes on 18 and 19)
        add_socket(rel, 'Hand ' + sd, np.array(WR[rel]), size=2.0, note="bionic wrist: centre by the wrist rule, roll from Mar Fil's hand on it")
        rep.append((rel, 'Arms', 'torso set %s (turned), disc on the joint' % k))
    elif folder == 'DoubleArms':
        if 'Cable' in b:
            entry(rel, 'Cables'); add_fit(rel, 'Cable', np.eye(4)); rep.append((rel, 'Cables', 'on its axe arms, as exported'))
            continue
        k = 'c' if num == '20' else 'd'; A = placed(POSE[k]['P'], POSE[k]['cR'], S_R)
        entry(rel, 'Two-Handed Melee'); add_fit(rel, 'Shoulder R', inv(S_R) @ A)
        add_socket(rel, 'Cable', np.eye(4), size=2.0, note='its cable, as exported')
        rep.append((rel, 'Two-Handed Melee', 'both arms + axe, torso set %s' % k))
    elif folder == 'Backpack':
        entry(rel, 'Backpacks'); add_fit(rel, 'Back', inv(S_BACK))
        add_socket(rel, 'Back Top', np.eye(4), note='forge gun mount (as exported, = Mar Fil build)')
        add_socket(rel, 'Servo Arm', T(SEATB), size=2.0, note="servo arm's shoulder ball centre, from Mar Fil's build file")
        add_socket(rel, 'Mechadendrite', np.eye(4), size=2.0, note='mechadendrites as exported')
        rep.append((rel, 'Backpacks', 'kit position + Back Top, Servo Arm, Mechadendrite'))
    elif folder == 'MechanicArms':
        c = np.array(BALLS[b]['c']); entry(rel, 'Servo Arms'); add_fit(rel, 'Servo Arm', T(-c))
        rep.append((rel, 'Servo Arms', 'ball (r 2.47) in the seat, as exported otherwise (moved %.1f mm)' % np.linalg.norm(SEATB - c)))
    elif folder == 'ExtensibleArms':
        entry(rel, 'Mechadendrites'); add_fit(rel, 'Mechadendrite', np.eye(4)); rep.append((rel, 'Mechadendrites', 'as exported'))
    elif folder == 'Weapons':
        if num in ('36', '37'):
            entry(rel, 'Backpack Toppers'); add_fit(rel, 'Back Top', np.eye(4)); rep.append((rel, 'Backpack Toppers', 'on the backpack mount, as exported'))
        else:
            sd = 'L' if num == '35' else 'R'; h = RU['hands'][b][sd]
            cat = 'Pistols' if num == '35' else 'Melee'; entry(rel, cat); add_fit(rel, 'Hand ' + sd, inv(np.array(h['M'])))
            rep.append((rel, cat, 'hand rule (fist %.3f)' % h['med']))
    elif folder == 'Accesories':
        if num == '38':
            W = np.array(RU['hands'][b]['L']['M']); entry(rel, 'Hands'); add_fit(rel, 'Hand L', inv(W))
            add_socket(rel, 'Grip L', W, size=2.0, note='wrist frame (hand rule): hand-less weapons go here')
            rep.append((rel, 'Hands', 'left hand by the hand rule + Grip L'))
        elif num == '42':
            entry(rel, 'Bases'); add_fit(rel, 'Base', np.eye(4)); rep.append((rel, 'Bases', 'under the legs, as exported'))
        else:
            rep.append((rel, 'belt', ''))       # below, with the legs
    elif folder in ('Shinpads', 'ShoulderPads'):
        v = PADS.get('All Mar All the time/' + rel)
        entry(rel, 'Knee Pads' if v['type'].startswith('Shin') else 'Shoulder Pads'); add_fit(rel, v['type'], np.array(v['fit']))
        rep.append((rel, side_data[rel]['category'], f"{v['type']} (match {v['median']:.2f})"))
    else:
        rep.append((rel, '-', 'not handled'))
# belt bits: exported on the legs (as exported, legs file = these coordinates). Frame where each touches the legs
def surf_n(V, Tr, n, seed=0):
    V = np.asarray(V, float); A_ = V[Tr]; cr = np.cross(A_[:, 1] - A_[:, 0], A_[:, 2] - A_[:, 0]); ar = np.linalg.norm(cr, axis=1); ok = ar > 0; A_, cr, ar = A_[ok], cr[ok], ar[ok]
    rng = np.random.default_rng(seed); i = rng.choice(len(A_), n, p=ar / ar.sum()); u, v = rng.random(n), rng.random(n); f = u + v > 1; u[f], v[f] = 1 - u[f], 1 - v[f]
    return A_[i, 0] + u[:, None] * (A_[i, 1] - A_[i, 0]) + v[:, None] * (A_[i, 2] - A_[i, 0]), cr[i] / ar[i, None]
LEGS = {rel: surf_n(*geo.load(rel), 300000) for rel in files if rel.split('/')[2] == 'Legs'}
for group in (('39-PistolHolster-1', '40-PistolHolster-2'), ('41-Pouch',)):
    a = group[0]; rel = O + 'Accesories/Raw-STL/' + a + '.stl'
    Q = np.concatenate([geo.surf(*geo.load(O + 'Accesories/Raw-STL/' + g + '.stl'), 40000) for g in group]); cq = Q.mean(0)
    pts, nrm, touching = [], [], []
    for lr, (Pl, Nl) in LEGS.items():
        d, i = cKDTree(Pl).query(Q)
        if d.min() > 0.1: continue
        touching.append(lr); k = d < d.min() + 0.15; pts.append(Q[k]); n_ = Nl[i[k]]; nrm.append(n_[((cq - Pl[i[k]]) * n_).sum(1) > 0])
    c = np.concatenate(pts).mean(0); z = np.concatenate(nrm).mean(0); y = np.array([0, 0, 1.0]); z = z - y * (z @ y); z /= np.linalg.norm(z)
    K = np.eye(4); K[:3, 0], K[:3, 1], K[:3, 2], K[:3, 3] = np.cross(y, z), y, z, c
    t = 'Hip L' if z[0] < -0.6 else 'Hip R' if z[0] > 0.6 else 'Belt Front' if z[1] > 0 else 'Belt Back'
    for g in group:
        gr = O + 'Accesories/Raw-STL/' + g + '.stl'; entry(gr, 'Accessories')
        for tt in ('Hip R', 'Hip L', 'Belt Front', 'Belt Back'): add_fit(gr, tt, inv(K))
        rep = [r for r in rep if r[0] != gr] + [(gr, 'Accessories', 'on the belt; Mar Fil spot (%s) on %d legs' % ('?', 0))]
    holds = '|'.join(group)
    for lr in touching:
        if not any((s.get('props') or {}).get('tiow_holds') == holds for s in entry(lr)['sockets']):
            add_socket(lr, t, K, size=1.5, note='where Mar Fil put ' + holds.replace('|', ' / '), props={'tiow_holds': holds}, keep=True)
    for g in group:
        gr = O + 'Accesories/Raw-STL/' + g + '.stl'
        rep = [r for r in rep if r[0] != gr] + [(gr, 'Accessories', 'on the belt; Mar Fil spot (%s) on %d legs' % (t, len(touching)))]
cnt = collections.Counter((r[1], re.sub(r'[\d.]+', '#', r[2])) for r in rep)
for k, n in sorted(cnt.items()): print('%3d  %-18s %s' % (n, k[0], k[1]))
json.dump({'side': side_data}, open('/home/claude/kits/tm/tm_partial.json', 'w'))
print(len(side_data), 'sidecars of', len(files), 'files')
import fix_belts; fix_belts.fix('/home/claude/kits/tm/tm_partial.json', '')   # belt anchors by rule, same frame on every kit's legs
