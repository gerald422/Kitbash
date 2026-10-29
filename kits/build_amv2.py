"""Sockets and fits for the AssaultMarines-V2 kit, written as <part>.sockets.json beside each raw STL
(into /home/claude/kits/out/, mirroring 'All Mar All the time')."""
import geo, json, numpy as np, os, glob, re, sys
from scipy.spatial import cKDTree
OUT = '/home/claude/kits/out/'
KIT = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
C = json.load(open('/home/claude/sock/carry.json'))
# objects named like "176-ChainSword-2-R.001" are the same file; the plain name wins
for _k in sorted(C, key=lambda k: (re.sub(r'\.\d{3}$', '', k), k != re.sub(r'\.\d{3}$', '', k))):
    C.setdefault(re.sub(r'\.\d{3}$', '', _k), C[_k])
D = json.load(open('/home/claude/blend/actual/dump.json'))
TM = {t['name']: np.array(t['mat']).reshape(4, 4) for t in D['scene']['types']}
MX = np.diag([-1.0, 1, 1, 1])
UP = '/mnt/user-data/uploads/new cults/All Mar All the time/'

def ortho(M):
    """drop scale/shear: keep rotation + translation"""
    M = np.array(M, float); U, S, Vt = np.linalg.svd(M[:3, :3]); R = U @ Vt
    if np.linalg.det(R) < 0: R = U @ np.diag([1, 1, -1]) @ Vt
    out = np.eye(4); out[:3, :3] = R; out[:3, 3] = M[:3, 3]; return out
def mirror_frame(S):  # a socket frame mirrored across x=0, kept right-handed
    return MX @ S @ MX
def flat(M): return [float(x) for x in np.asarray(M).reshape(-1)]
def sockets_of(name):
    c = C[name]; Ti = np.linalg.inv(np.array(c['T']))
    return {s['type']: Ti @ np.array(s['matrix']).reshape(4, 4) for s in (c['sidecar'] or {}).get('sockets', [])}

side_data = {}          # rel -> sidecar dict
def entry(rel, category=None):
    d = side_data.setdefault(rel, {'schemaVersion': 1, 'part': os.path.splitext(os.path.basename(rel))[0], 'sockets': [], 'fits': {}})
    if category: d['category'] = category
    return d
def add_socket(rel, tname, M, size=3.0, note=None):
    d = entry(rel)
    d['sockets'] = [s for s in d['sockets'] if s['type'] != tname]
    s = {'type': tname, 'name': f"{d['part']}_socket_{tname}", 'matrix': flat(ortho(M)), 'display_type': 'ARROWS', 'display_size': size, 'props': {'tiow_from': note} if note else {}}
    d['sockets'].append(s)
def add_fit(rel, tname, F): entry(rel)['fits'][tname] = flat(ortho(F))
def files(sub): return sorted(f.split(geo.RAW)[1] for f in glob.glob(geo.RAW + KIT + sub + '/*.stl'))
def by_num(paths):
    out = {}
    for p in paths:
        m = re.search(r'(\d+)-', os.path.basename(p)); out.setdefault(int(m.group(1)), []).append(p)
    return out

# ---------------- torso sockets (all 6 torsos share the joints, checked to 0.03 mm)
TS = sockets_of('23-Torso-2.001')
S_R = ortho(TS['arm__Torso_r'] @ TM['arm__Torso_r'])
S_L = mirror_frame(S_R)
S_NECK = ortho(TS['Head'])
S_BACK = ortho(TS['Backpack'])
S_WAIST = ortho(TS['Legs to chest'])
for rel in files('Chest'):
    entry(rel, 'Chests')
    add_socket(rel, 'Shoulder R', S_R, note='3rd attempt: arm__Torso_r')
    add_socket(rel, 'Shoulder L', S_L, note='mirror of Shoulder R')
    add_socket(rel, 'Neck', S_NECK, note='3rd attempt: Head')
    add_socket(rel, 'Back', S_BACK, note='3rd attempt: Backpack')
    add_socket(rel, 'Waist', S_WAIST, note='3rd attempt: Legs to chest')

# ---------------- right arms (all 24 in Josh's file)
R_ARMS = {}
for rel in files('Arms'):
    n = os.path.splitext(os.path.basename(rel))[0]
    if '-R-' not in n: continue
    c = C[n]; T = np.array(c['T']); Ti = np.linalg.inv(T)
    entry(rel, 'Arms'); add_fit(rel, 'Shoulder R', T)
    S = sockets_of(n)
    hand = ortho(S['Wrist_socket_r'] @ TM['Wrist_socket_r'])
    add_socket(rel, 'Hand R', hand, note='3rd attempt: Wrist_socket_r')
    fore = None
    if 'Wrist_Armout_r' in S:
        fore = ortho(S['Wrist_Armout_r'] @ ortho(TM['Wrist_Armout_r']))
        add_socket(rel, 'Forearm R', fore, note='3rd attempt: Wrist_Armout_r')
    R_ARMS[n] = (T, hand, fore)
# ---------------- left arms: X-mirrors of the right B arm of the same design, moved along x
LA = json.load(open('/home/claude/kits/b_arms2.json'))
for rel in files('Arms'):
    n = os.path.splitext(os.path.basename(rel))[0]
    if '-L-' not in n: continue
    a = LA[n]; A = geo.M4(np.array(a['R']), np.array(a['t']))        # L = A @ MX @ RB
    T, hand, fore = R_ARMS[a['src']]
    entry(rel, 'Arms')
    add_fit(rel, 'Shoulder L', MX @ T @ MX @ np.linalg.inv(A))
    add_socket(rel, 'Hand L', A @ MX @ hand @ MX, note='mirror of ' + a['src'])
    if fore is not None: add_socket(rel, 'Forearm L', A @ MX @ fore @ MX, note='mirror of ' + a['src'])

# ---------------- hand-held: melee, shield, pistols (right files in Josh's file use his fits)
SHARED = np.array(C['211-BoltPistol-R']['T'])          # Mar Fil's grip, as Josh set it on the pistols
GM = json.load(open('/home/claude/kits/g_mirror.json'))
def mirror_move(lrel, rrel):
    """A with L = A @ MX @ R (L file vs the right file)"""
    V, T = geo.load(rrel); W, U = geo.load(lrel)
    S = geo.surf(V * [-1, 1, 1], T[:, ::-1], 150000); P = geo.surf(W, U, 3000)
    R, t, d = geo.icp(P, cKDTree(S), S, np.eye(3), np.zeros(3), 60)
    return np.linalg.inv(geo.M4(R, t)), float(np.median(d))
held_report = []
for sub, lsub in (('Melee', 'Melee/LeftOrientated'), ('Pistols', 'Pistols/LeftOrientated')):
    R_files = by_num(files(sub)); L_files = by_num(files(lsub))
    for num, rr in R_files.items():
        rrel = rr[0]; n = os.path.splitext(os.path.basename(rrel))[0]
        cat = 'Shields' if 'Shield' in n else ('Pistols' if sub == 'Pistols' else 'Melee')
        F = np.array(C[n]['T']) if n in C else SHARED
        entry(rrel, cat); add_fit(rrel, 'Hand R', F)
        held_report.append((n, 'yours' if n in C else 'shared grip'))
        for lrel in L_files.get(num, []):
            A, med = mirror_move(lrel, rrel)
            entry(lrel, cat); add_fit(lrel, 'Hand L', MX @ F @ MX @ np.linalg.inv(A))

# ---------------- power fists: whole arms. Main folder = right arms, Mirrored = left arms; joint = inner face on the shoulder axis
import joint
for rel in files('PowerFist'):
    V, T = geo.load(rel); x = joint.inner_x(V, 'R')
    entry(rel, 'Arms'); add_fit(rel, 'Shoulder R', geo.M4(np.eye(3), -np.array([x, 0.2, 31.95])) @ np.eye(4))
    # match Josh's arms: joint at the socket (his arm fits put the joint exactly on Shoulder R)
for rel in files('PowerFist/Mirrored'):
    V, T = geo.load(rel); x = joint.inner_x(V, 'L')
    entry(rel, 'Arms'); add_fit(rel, 'Shoulder L', geo.M4(np.eye(3), -np.array([x, 0.2, 31.95])))

# ---------------- two-handed weapons: both arms, in kit position on the torso
for rel in files('TwoHandedWeapons'):
    entry(rel, 'Two-Handed Melee'); add_fit(rel, 'Shoulder R', np.linalg.inv(S_R))

# ---------------- helmets and heads: one shared frame, Josh's 1-Helmet-1 fit
FH = TM['Head'] @ np.array(C['1-Helmet-1']['T'])
for rel in files('Helmet-Heads'):
    entry(rel, 'Heads'); add_fit(rel, 'Neck', FH)

# ---------------- jump packs (Mar Fil's kit position) with fin mounts; fins are left pieces in kit position
J = sockets_of('55-JumpPack-1')
FIN_L = ortho(J['BackPack_fin_l'] @ TM['BackPack_fin_l'])
FIN_R = mirror_frame(FIN_L)
for rel in files('JumpPacks'):
    n = os.path.basename(rel)
    if 'Fin' in n:
        entry(rel, 'Pack Fins'); add_fit(rel, 'Pack Fin L', np.linalg.inv(FIN_L))
    else:
        entry(rel, 'Jump Packs'); add_fit(rel, 'Back', np.linalg.inv(S_BACK))
        add_socket(rel, 'Pack Fin L', FIN_L, note="3rd attempt: 55's BackPack_fin_l")
        add_socket(rel, 'Pack Fin R', FIN_R, note='mirror of Pack Fin L')

# ---------------- legs: torso set on each as Josh did it (his Chest-to-legs sockets, posing for claude.blend);
# 28 gets his average; Mirrored files are the mirror of their original
LJ = json.load(open('/home/claude/kits/legs_josh.json')); LM = json.load(open('/home/claude/kits/legs_mirror.json'))
LIP = json.load(open('/home/claude/kits/lip_seat2.json'))
Davg = np.array(LJ['Davg'])
SWi = np.linalg.inv(S_WAIST)
legs_M, legs_hips = {}, {}
for sub in ('Legs', 'Legs(JumpPack)'):
    for rel in files(sub):
        if rel in LJ['legs']:
            legs_M[rel] = np.array(LJ['legs'][rel]['M']); legs_hips[rel] = {k: np.array(v) for k, v in LJ['legs'][rel]['hips'].items() if k.startswith('Hip')}
        else:
            legs_M[rel] = Davg @ np.array(LIP[rel]['M']); legs_hips[rel] = {}
for sub in ('Legs', 'Legs(JumpPack)'):
    for mrel in files(sub + '/Mirrored'):
        m = LM[mrel]; A = np.array(m['A']); o = m['orig']
        legs_M[mrel] = MX @ legs_M[o] @ MX @ np.linalg.inv(A)
        legs_hips[mrel] = {('Hip R' if k == 'Hip L' else 'Hip L'): A @ MX @ H @ MX for k, H in legs_hips[o].items()}
for rel, M in legs_M.items():
    entry(rel, 'Legs'); add_fit(rel, 'Waist', SWi @ M)
    add_socket(rel, 'Base', np.eye(4), note='legs file origin')
    for k, H in legs_hips[rel].items():
        add_socket(rel, k, H, note='Legs donrrr: ' + ('Right Hip' if k == 'Hip R' else 'Left Hip'))

# ---------------- Pad anchors worked out offline (full swing search; the import-time copy misses arm 3 and some fists)
if os.path.exists('/home/claude/kits/pads_offline.json'):
    for rel, s in json.load(open('/home/claude/kits/pads_offline.json'))['anchors'].items():
        d = entry(rel); d['sockets'] = [x for x in d['sockets'] if x['type'] != s['type']] + [s]

json.dump({'side': side_data, 'S_WAIST': S_WAIST.tolist(), 'held': held_report}, open('/home/claude/kits/amv2_partial.json', 'w'))
print(len(side_data), 'sidecars so far;', sum(1 for h in held_report if h[1] == 'shared grip'), 'right-hand weapons on the shared grip:', [h[0] for h in held_report if h[1] == 'shared grip'])
import fix_belts; fix_belts.fix('/home/claude/kits/amv2_partial.json', '')   # belt anchors by rule, same frame on every kit's legs
