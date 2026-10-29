"""Sidecars for Veteran Squad (VS) and Veteran Blade Squad (VBS): same torso joints as the Assault Marines kit,
everything else in Mar Fil's kit position (Josh: torso as exported, it already sits on the legs), hand-held parts by rule."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, glob, re
from scipy.spatial import cKDTree
MX = np.diag([-1.0, 1, 1, 1])
P = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
TOR = {s['type']: np.array(s['matrix']).reshape(4, 4) for s in P['AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/22-Torso-1.stl']['sockets']}
S_R, S_L, S_NECK, S_BACK, S_WAIST = (TOR[k] for k in ('Shoulder R', 'Shoulder L', 'Neck', 'Back', 'Waist'))
inv = np.linalg.inv
J_ARM = np.array([5.568, 0.202, 31.949])          # Josh's Bladeguard arms: inner face on the shoulder axis (all Vet/BG arms share it)
ARM_R = geo.M4(np.eye(3), -J_ARM); ARM_L = geo.M4(np.eye(3), -J_ARM * [-1, 1, 1])
C = json.load(open('/home/claude/sock/carry.json'))
S_TOP = np.array(C['1']['sidecar']['sockets'][0]['matrix']).reshape(4, 4)   # Josh's 'Primaris back pack topper' on Vet backpack 1 (kit frame)
S_CABLE = geo.M4(np.eye(3), np.array([7.0, 1.0, 22.0]))                    # heavy weapon cable mount (kit frame; cables are in kit position)
AMH = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/Helmet-Heads/1-Helmet-1.stl'
F_AMH = np.array(P[AMH]['fits']['Neck']).reshape(4, 4)
SEAT = json.load(open('/home/claude/kits/vet/legs_seat.json'))

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
    """Neck fit for a helmet folder: the AM-V2 helmet (Josh's fit) matched onto this kit's matching helmet."""
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

def kit(name, base, files):
    """files: paths relative to 'All Mar All the time' (base = where the meshes are, for the ones that need a look)"""
    rep = []
    def bb(rel):
        try: V, T = geo.load(rel)
        except FileNotFoundError: return None
        return V.min(0), V.max(0)
    for rel in files:
        f = os.path.basename(rel); low = rel.lower(); mir = 'mirrored' in low
        num = int(re.match(r'(\d+)', f).group(1)) if re.match(r'(\d+)', f) else None
        if '/body/' in low:
            if 'chest' in f.lower():
                entry(rel, 'Chests')
                for t, S in (('Shoulder R', S_R), ('Shoulder L', S_L), ('Neck', S_NECK), ('Back', S_BACK), ('Waist', S_WAIST)):
                    add_socket(rel, t, S, note='Assault Marines torso joints (kit frame shared)')
                rep.append((rel, 'Chests', 'torso sockets'))
            else:
                entry(rel, 'Legs'); add_socket(rel, 'Base', np.eye(4), note='legs file origin')
                st = SEAT[rel]                      # seated like Josh's AM-V2 legs (the orange version he picked)
                add_fit(rel, 'Waist', inv(S_WAIST) @ np.array(st['M']))
                for h, H in st['hips'].items(): add_socket(rel, h, H, note='hip, from ' + os.path.basename(st['ref']))
                rep.append((rel, 'Legs', 'seated like ' + os.path.basename(st['ref'])))
        elif '/arms/' in low:
            entry(rel, 'Arms'); add_fit(rel, 'Shoulder L' if mir else 'Shoulder R', ARM_L if mir else ARM_R)
            rep.append((rel, 'Arms', 'joint at the inner face'))
        elif 'powerfist' in low:            # Vet power fists: left arms in kit position
            entry(rel, 'Arms'); add_fit(rel, 'Shoulder L', ARM_L); rep.append((rel, 'Arms', 'power fist, left'))
        elif '/additional/' in low:             # Bladeguard 159/160: a left arm holding a sword, in kit position
            b = bb(rel); left = b is not None and b[1][0] < -3
            entry(rel, 'Arms'); add_fit(rel, 'Shoulder L' if left else 'Shoulder R', ARM_L if left else ARM_R); rep.append((rel, 'Arms', 'arm with sword'))
        elif '/melee/' in low or '/shields/' in low:
            cat = 'Shields' if '/shields/' in low else 'Melee'
            entry(rel, cat); rep.append((rel, cat, 'hand rule'))
        elif '/doublehandedmelee/' in low:
            entry(rel, 'Two-Handed Melee'); add_fit(rel, 'Shoulder R', inv(S_R)); rep.append((rel, 'Two-Handed Melee', 'kit position'))
        elif '/heavyweapons/' in low:
            if 'cable' in low or 'newversion' in low:
                if num == 174: rep.append((rel, '-', 'unknown bit, skipped')); continue
                entry(rel, 'Heavy Weapon Cables'); add_fit(rel, 'Cable', inv(S_CABLE)); rep.append((rel, 'Heavy Weapon Cables', 'kit position'))
            else:
                entry(rel, 'Heavy Weapons'); add_fit(rel, 'Shoulder R', inv(S_R)); add_socket(rel, 'Cable', S_CABLE, note='cable mount (kit frame)')
                rep.append((rel, 'Heavy Weapons', 'kit position'))
        elif '/weapons/' in low:
            b = bb(rel)
            if b is None: entry(rel, 'Pistols'); rep.append((rel, 'Pistols', 'hand rule (not looked at)')); continue
            lo, hi = b
            if hi[2] > 15 and (lo[0] > 3 or hi[0] < -3):          # an arm holding a gun, in kit position, one side
                left = hi[0] < -3
                entry(rel, 'Arms'); add_fit(rel, 'Shoulder L' if left else 'Shoulder R', ARM_L if left else ARM_R); rep.append((rel, 'Arms', 'arm with gun'))
            elif hi[2] > 15:
                entry(rel, 'Two-Handed Guns'); add_fit(rel, 'Shoulder R', inv(S_R)); rep.append((rel, 'Two-Handed Guns', 'kit position'))
            else:
                entry(rel, 'Pistols'); rep.append((rel, 'Pistols', 'hand rule'))
        elif '/backpack' in low:
            b = bb(rel); topper = b is not None and b[0][2] > 36.5
            if topper:
                entry(rel, 'Backpack Toppers'); add_fit(rel, 'Back Top', inv(S_TOP)); rep.append((rel, 'Backpack Toppers', 'kit position'))
            else:
                entry(rel, 'Backpacks'); add_fit(rel, 'Back', inv(S_BACK)); add_socket(rel, 'Back Top', S_TOP, note="Josh's topper socket (Vet backpack 1)")
                rep.append((rel, 'Backpacks', 'kit position'))
        elif '/helmet' in low:
            entry(rel, 'Heads'); rep.append((rel, 'Heads', 'folder neck fit'))
        elif 'shinpad' in low.replace('-', '') or 'shoulderpad' in low.replace('-', ''):
            pass                                   # pads: separate step
        else:
            rep.append((rel, '-', 'not handled'))
    return rep

VS = sorted(f[len(geo.RAW):] for f in glob.glob(geo.RAW + 'VeteranSquad/VeteranSquad/**/*.stl', recursive=True) if '/NewBits/' not in f and '/Accesories/' not in f)
VBS = []
for line in open('/home/claude/kits/vet/vbs_list.txt'):
    d, fs = line.split(':', 1)
    VBS += ['VeteranBladeSquad/VeteranBladeSquad/' + d.strip() + '/' + f for f in fs.split()]
rep = kit('VS', geo.RAW, VS) + kit('VBS', geo.U, VBS)
# helmet folders: one Neck fit each
for folder, ref in (('VeteranSquad/VeteranSquad/Helmets/Helmet-RawStl/', '1-Helmet-A.stl'), ('VeteranBladeSquad/VeteranBladeSquad/Helmets/Helmets-RawSTL/', '1-Helmet-1-A.stl')):
    F, md = neck_fit(folder + ref)
    for rel in [r for r in side_data if r.startswith(folder)]: add_fit(rel, 'Neck', F)
    print('Neck fit for', folder, 'from', ref, 'match %.3f' % md)
import collections
cnt = collections.Counter((r[0].split('/')[0], r[1], r[2]) for r in rep)
for k, n in sorted(cnt.items()): print('%3d  %-20s %-22s %s' % (n, k[0], k[1], k[2]))
json.dump({'side': side_data}, open('/home/claude/kits/vet/vet_partial.json', 'w'))
print(len(side_data), 'sidecars')
import fix_belts; fix_belts.fix('/home/claude/kits/vet/vet_partial.json', '')   # belt anchors by rule, same frame on every kit's legs
