"""Sidecars for Mar Fil's Outriders (All Mar All the time\\Outriders (1)). Same joints as every other kit: torsos = the
AM torso sockets; legs seated like Josh's AM legs; the legs, arms and bike are exported together in the bike's frame, so
each arm goes on the shoulder exactly as Mar Fil assembled it on its legs (arms laid out to one side for export are
moved back by their sideways shift); the bike's rear body sits on the legs and carries one socket per bike part."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, re, glob, collections
inv = np.linalg.inv; MX = np.diag([-1.0, 1, 1, 1])
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
TOR = {s['type']: np.array(s['matrix']).reshape(4, 4) for s in P['AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/22-Torso-1.stl']['sockets']}
S_R, S_L, S_NECK, S_BACK, S_WAIST = (TOR[k] for k in ('Shoulder R', 'Shoulder L', 'Neck', 'Back', 'Waist'))
O = "Outriders (1)/Outriders/"
SEAT = json.load(open('/home/claude/kits/or/legs_seat.json'))
LEGS = {os.path.basename(k)[:-4]: np.array(v['M']) for k, v in SEAT.items()}
D = json.load(open('/home/claude/kits/or/discs.json'))
H = json.load(open('/home/claude/kits/or/hands.json'))
PADS = json.load(open('/home/claude/kits/or/or_pads.json'))
side_data = {}
def entry(rel, category=None):
    d = side_data.setdefault(rel, {'schemaVersion': 1, 'part': os.path.splitext(os.path.basename(rel))[0], 'sockets': [], 'fits': {}})
    if category: d['category'] = category
    return d
def flat(M): return [float(x) for x in np.asarray(M).reshape(-1)]
def add_socket(rel, tname, M, size=3.0, note=None, props=None):
    d = entry(rel); d['sockets'] = [s for s in d['sockets'] if s['type'] != tname]
    pr = dict(props or {})
    if note: pr['tiow_from'] = note
    d['sockets'].append({'type': tname, 'name': f"{d['part']}_socket_{tname}", 'matrix': flat(M), 'display_type': 'ARROWS', 'display_size': size, 'props': pr})
def add_fit(rel, tname, F): entry(rel)['fits'][tname] = flat(F)
def T(x=0.0, y=0.0, z=0.0): M = np.eye(4); M[:3, 3] = (x, y, z); return M
rep = []
files = sorted(os.path.relpath(f, geo.U) for f in glob.glob(geo.U + O + '**/*.stl', recursive=True))
# ---- arms: which legs each belongs to (its shoulder face fits that pose: 0.3-4 deg, next best 5-22), export shift
J = np.array([5.484, 0.202, 31.949])
def arm_legs(b, sd):
    if 'Handle' in b:
        L = re.search(r'-(Right|Left)-([A-F])', b).group(2); n = 'ABCDEF'.index(L) + 1
        return f"{n}-Legs-{L}" + ('-Mirrored' if sd == 'L' and L != 'A' else '')
    n = int(b.split('-')[0]) - 12; L = 'ABCDEF'[n - 1]
    return f"{n}-Legs-{L}" + ('-Mirrored' if sd == 'R' and L != 'A' else '')
def partner(b):     # the mirror-image arm (right <-> left) of the same pose
    if 'Handle-Right' in b: return b.replace('ArmWithHandle-Right', 'ArmWightHandle-Left').replace('.stl', '-1.stl')
    if 'Handle-Left' in b: return re.sub(r'-[12]\.stl$', '.stl', b.replace('ArmWightHandle-Left', 'ArmWithHandle-Right'))
    if 'Mirrored' in b: return re.sub(r'-Mirrored-[AB]\.stl$', '.stl', b)
    return b.replace('.stl', '-Mirrored-A.stl')
OFF = {}
for a, ds in D.items():
    b = os.path.basename(a); sd = 'L' if ('Left' in b or 'Mirrored' in b) else 'R'
    M = LEGS[arm_legs(b, sd)]; want = inv(M) @ np.r_[J * ([1, 1, 1] if sd == 'R' else [-1, 1, 1]), 1]
    OFF[b] = np.array(ds[0]['c']) - want[:3]
for rel in files:
    sub = rel[len(O):]; b = os.path.basename(rel)
    if sub.startswith('Torsos/'):
        entry(rel, 'Chests')
        for t, S in (('Shoulder R', S_R), ('Shoulder L', S_L), ('Neck', S_NECK), ('Back', S_BACK), ('Waist', S_WAIST)):
            add_socket(rel, t, S, note='Assault Marines torso joints (the Outrider torso matches at every joint)')
        rep.append((rel, 'Chests', 'torso sockets'))
    elif sub.startswith('Legs/'):
        M = LEGS[b[:-4]]; entry(rel, 'Legs'); add_fit(rel, 'Waist', inv(S_WAIST) @ M)
        add_socket(rel, 'Base', np.eye(4), note='legs file origin (the bike frame): the base')
        add_socket(rel, 'Bike', np.eye(4), note='the bike, as Mar Fil exported it under these legs')
        rep.append((rel, 'Legs', "seated like Josh's AM legs, + Bike"))
    elif sub.startswith(('Arms/', 'Arms(WithHandles)/')):
        sd = 'L' if ('Left' in b or 'Mirrored' in b) else 'R'; M = LEGS[arm_legs(b, sd)]
        off = OFF[b]; shift = 0.0
        if abs(off[1]) > 1.0:                                   # laid out to the side for export
            shift = off[1] + OFF[partner(b)][1]                  # minus the seat residual its mirror twin shows
        F = inv(S_R if sd == 'R' else S_L) @ M @ T(0, -shift, 0)
        entry(rel, 'Arms'); add_fit(rel, 'Shoulder ' + sd, F)
        joint_err = np.linalg.norm((F @ np.r_[D[rel][0]['c'], 1])[:3])
        rep.append((rel, 'Arms', 'as assembled on its legs' + (' (moved back %.2f mm)' % shift if shift else '') + ', disc %.1f mm from the joint' % joint_err))
    elif sub.startswith('Weapons/'):
        sd = 'L' if 'Mirrored' in b else 'R'
        if 'NoHand' in b:
            num = int(b.split('-')[0]); A = [k for k in H if os.path.basename(k).startswith('%d-' % (num - 2)) and 'Mirrored' not in k][0]
            W = np.array(H[A]['R']['M'])
            entry(rel, 'Hand-less Weapons'); add_fit(rel, 'Grip R', inv(W)); add_fit(rel, 'Grip L', inv(MX @ W @ MX))
            rep.append((rel, 'Hand-less Weapons', 'grip as in its with-hand A version (%s)' % os.path.basename(A)))
        else:
            h = H[rel][sd]; cat = 'Pistols' if 'Pistol' in b else 'Melee'
            entry(rel, cat); add_fit(rel, 'Hand ' + sd, inv(np.array(h['M']))); rep.append((rel, cat, 'hand rule (fist %.3f)' % h['med']))
    elif sub.startswith('Bike/'):
        if b.startswith('19-'):
            entry(rel, 'Bikes'); add_fit(rel, 'Bike', np.eye(4))
            for t, holds in (('Bike Front', '21-Body-2'), ('Front Wing', '22-FrontWing'), ('Front Wheel', '23-FrontWheel'), ('Rear Wheel', '24-RearWheel'),
                             ('Exhaust R', '25-ExhaustRight'), ('Exhaust L', '26-ExhaustLeft'), ('Handle R', '29-HandleRight'), ('Handle L', '30-HandleLeft'),
                             ('Bike Guns', '31-BoltersTwins|32-PlasmaTwins')):
                add_socket(rel, t, np.eye(4), size=2.0, note='bike part as exported', props={'tiow_holds': holds})
            rep.append((rel, 'Bikes', 'on the legs, sockets for the bike parts'))
        else:
            t = {'21': 'Bike Front', '22': 'Front Wing', '23': 'Front Wheel', '24': 'Rear Wheel', '25': 'Exhaust R', '26': 'Exhaust L', '29': 'Handle R', '30': 'Handle L', '31': 'Bike Guns', '32': 'Bike Guns'}[b.split('-')[0]]
            entry(rel, 'Bike Parts'); add_fit(rel, t, np.eye(4)); rep.append((rel, 'Bike Parts', t))
    elif b.startswith('Base-'):
        c, s_ = 0.0, 1.0; Rz = np.array([[c, -s_, 0, 0], [s_, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
        entry(rel, 'Bases'); add_fit(rel, 'Base', T(-29.6, 0, -14.37) @ Rz); rep.append((rel, 'Bases', 'under the bike, wheels on it'))
    elif sub.startswith(('ShinPads/', 'ShoulderPads/')):
        v = PADS.get('All Mar All the time/' + rel)
        if v is None: rep.append((rel, '-', 'pad not matched')); continue
        entry(rel, 'Knee Pads' if v['type'].startswith('Shin') else 'Shoulder Pads'); add_fit(rel, v['type'], np.array(v['fit']))
        rep.append((rel, side_data[rel]['category'], f"{v['type']} (match {v['median']:.2f})"))
    elif sub.startswith('Accesories/'):
        # belt bits: decorated face +y (the -Mirrored holsters: -y), flat back on the belt; up +z (holsters +x)
        V, Tr = geo.load(rel); Q = geo.surf(V, Tr, 60000)
        out = np.array([0, -1.0, 0]) if 'Mirrored' in b else np.array([0, 1.0, 0])
        up = np.array([1.0, 0, 0]) if 'Holster' in b else np.array([0, 0, 1.0])
        h = Q @ up; h0 = h.max() - (h.max() - h.min()) / 3.0
        dep = Q @ out; back = Q[(dep < dep.min() + 0.35) & (np.abs(h - h0) < 1.0)]
        if not len(back): back = Q[dep < dep.min() + 0.35]
        o = back.mean(0); o = o - out * (o @ out - dep.min())
        K = np.eye(4); K[:3, 0], K[:3, 1], K[:3, 2], K[:3, 3] = np.cross(up, out), up, out, o
        cat = 'Seals' if 'PuritySeal' in b else 'Accessories'; entry(rel, cat)
        for t in ('Hip R', 'Hip L', 'Belt Front', 'Belt Back'): add_fit(rel, t, inv(K))
        rep.append((rel, cat, 'back on the belt, Y up (any belt anchor)'))
    else:
        rep.append((rel, '-', 'not handled'))
cnt = collections.Counter((r[1], re.sub(r'[\d.]+', '#', r[2])) for r in rep)
for k, n in sorted(cnt.items()): print('%3d  %-18s %s' % (n, k[0], k[1]))
for r in rep:
    if r[1] == 'Arms' and 'moved' in r[2] or r[1] == '-': print('    ', os.path.basename(r[0]), r[2])
json.dump({'side': side_data}, open('/home/claude/kits/or/or_partial.json', 'w'))
print(len(side_data), 'sidecars of', len(files), 'files')
import fix_belts; fix_belts.fix('/home/claude/kits/or/or_partial.json', '')   # belt anchors by rule, same frame on every kit's legs
