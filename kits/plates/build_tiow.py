"""Library files for plates, buckle, sheaths, tabards and trophies on the Mar Fil Assault legs (TIOW Inbox 1.17.6).
Reads marfil_assault_plates.json (all the placements Josh checked on Nov 3) and the repo's library sidecars;
writes new parts (STL + sidecar), changed sidecars and the _sources.csv rows under OUT."""
import os, sys, json, shutil, glob, numpy as np
REPO = '/home/claude/kitbash'; LIB = REPO + '/library'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/outputs/plates-tiow-2026-11-03/lib'
NC = '/mnt/user-data/uploads/d/new cults/'
doc = json.load(open(REPO + '/kits/plates/marfil_assault_plates.json'))
M16 = lambda a: np.array(a, float).reshape(4, 4)
L = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
A = np.diag([-1.0, 1, 1, 1])                          # the mirror variants' align: x -> -x
mir = lambda X: A @ X @ A                             # a frame or fit for the left, as it is in the mirrored file
inv = np.linalg.inv
DIR = 'Mar Fil - Tacticus\\AssaultMarines-V2\\'
PLATE = DIR + 'Hip Plates\\MarFil Assault - Hip Plate L.stl'
BUCKLE = DIR + 'Buckles\\MarFil Assault - Buckle.stl'
SHEATH = DIR + 'Holsters\\MarFil Assault - Pistol Sheath %d L.stl'
CBL = 'CyberBrush - Tacticus\\Space Bugs Hunters\\Space Bug Hunters Loinclothes\\Accessories\\CyberBrush Bug Hunters - Loinclothe %d.stl'
CBD = 'CyberBrush - Tacticus\\Space Bugs Hunters\\Space Bug Hunters Belt Decorations\\Accessories\\CyberBrush Bug Hunters - Belt Decoration %d.stl'
nat = lambda rel: rel.replace('\\', '/')
side_json = lambda rel: os.path.splitext(nat(rel))[0] + '.sockets.json'

def write_like(rel, d, like=None):
    """Write a sidecar in the same style as the file it replaces (CRLF or LF, indent), new ones indent 1 + LF."""
    p = os.path.join(OUT, side_json(rel)); os.makedirs(os.path.dirname(p), exist_ok=True)
    nl, ind = '\n', 1
    if like and os.path.isfile(like):
        raw = open(like, 'rb').read().decode('utf-8')
        nl = '\r\n' if '\r\n' in raw else '\n'
        second = raw.split(nl)[1] if nl in raw else ''
        ind = len(second) - len(second.lstrip(' ')) or None
    txt = json.dumps(d, indent=ind, ensure_ascii=False)
    if nl != '\n': txt = txt.replace('\n', nl)
    open(p, 'wb').write(txt.encode('utf-8'))
def copy_stl(src, rel):
    p = os.path.join(OUT, nat(rel)); os.makedirs(os.path.dirname(p), exist_ok=True); shutil.copyfile(src, p)
def sock(t, M, why, size=1.5):
    return {'type': t, 'name': t, 'matrix': L(M), 'display_type': 'ARROWS', 'display_size': size, 'props': {'tiow_from': why}}
rows = []

# ---- the hip plate (left as its file; the right is its mirror image)
Pc = M16(doc['plate_frame']['matrix']); Sm = M16(doc['plate_self_mirror']['matrix']); S_wp = M16(doc['holster_socket_on_plate']['matrix'])
copy_stl(NC + 'All Mar All the time/AssaultMarines-V2/WaistPlate.stl', PLATE)
write_like(PLATE, {'schemaVersion': 1, 'part': 'WaistPlate', 'category': 'Hip Plates',
    'sockets': [sock('Plate Hang L', S_wp, "Josh's holster spot on the plate (holster check 4A.blend, Nov 3)", 2.0)],
    'fits': {'Plate L': L(inv(Pc))},
    'notes': {'Plate L': 'sits exactly where the Assault B legs have it sculpted (registered, 0.03-0.05 mm); seated on the standing legs',
              'type': 'hip plates are always on: holsters and sheaths hang from their Plate Hang socket (TIOW Inbox 1.17.6)'},
    'variants': [{'side': 'R', 'mirror': True, 'align': L(A), 'name': 'MarFil Assault - Hip Plate R', 'title': 'MarFil Assault - Hip Plate R',
                  'folder': 'Hip Plates', 'from': 'mirror (the plate is symmetric: its mirror image fits the right hip as exactly)',
                  'sidecar': {'category': 'Hip Plates', 'fits': {'Plate R': L(inv(mir(Pc)))},
                              'sockets': [sock('Plate Hang R', mir(S_wp), 'mirror of the left plate\'s holster spot', 2.0)]}}],
    'original': {'name': 'WaistPlate', 'folder': 'AssaultMarines-V2', 'path': 'new cults\\All Mar All the time\\AssaultMarines-V2\\WaistPlate.stl'}})
rows.append((PLATE, 'All Mar All the time\\AssaultMarines-V2\\WaistPlate.stl', 'Hip Plates'))

# ---- the buckle (Josh's, separated from the Mar Fil Techmarine build file's waist)
bp = doc['buckle_part']['sockets']; ORN = M16(bp['Buckle Ornament']['matrix']); TAB = M16(bp['Tabard']['matrix'])
copy_stl('/mnt/user-data/uploads/Desktop/buckle.stl', BUCKLE)
write_like(BUCKLE, {'schemaVersion': 1, 'part': 'buckle', 'category': 'Buckles',
    'sockets': [sock('Tabard', TAB, 'back-bottom of the buckle: tabards hang from here (Josh, tabard check1.blend)', 1.5),
                sock('Buckle Ornament', ORN, 'the face of the boss (the buckle spot Josh set on Standing 2)', 1.5)],
    'fits': {'Buckle': L(inv(ORN))},
    'notes': {'Buckle': 'on the legs\' Buckle socket it sits exactly on the sculpted buckle (shape match 0.03 mm; 8A placed by Josh)',
              'type': 'Josh separated it from the Mar Fil Techmarine build file (Desktop buckle.stl, Nov 3); prints on its own'},
    'original': {'name': 'buckle', 'folder': 'Desktop', 'path': '~\\Desktop\\buckle.stl'}})
rows.append((BUCKLE, "Josh's Desktop buckle.stl (separated from the Mar Fil Techmarine build file)", 'Buckles'))

# ---- the six Mar Fil pistol sheaths (one body, same file frame): on the plate's Plate Hang socket
SF = M16(doc['sheath_fit_on_plate_socket']['matrix'])
for n, raw in enumerate(['215-SheatPistol-1', '216-SheatPistol-2', '217-SheatPistol-3', '218-SheatPistol-4', '219-SheatPistol-5', '220-SheatPistol-6'], 1):
    rel = SHEATH % n; src = 'All Mar All the time\\AssaultMarines-V2\\AssaultMarines-V2\\RawSTL\\Accesory\\%s.stl' % raw
    copy_stl(NC + nat(src), rel)
    write_like(rel, {'schemaVersion': 1, 'part': raw, 'category': 'Plate Accessories', 'sockets': [],
        'fits': {'Plate Hang L': L(SF)}, 'adaptor': PLATE,
        'notes': {'Plate Hang L': "Josh's placement on the left plate (sheath check 4A.blend, Nov 3); the six share one body",
                  'adaptor': 'comes with its hip plate when the legs have none yet'},
        'variants': [{'side': 'R', 'mirror': True, 'align': L(A), 'name': 'MarFil Assault - Pistol Sheath %d R' % n, 'title': 'MarFil Assault - Pistol Sheath %d R' % n,
                      'folder': 'Holsters', 'from': 'mirror of the left sheath (Josh, Nov 3: mirrored copies for the right)',
                      'sidecar': {'category': 'Plate Accessories', 'sockets': [], 'fits': {'Plate Hang R': L(mir(SF))}}}],
        'original': {'name': raw, 'folder': 'Accesory', 'path': 'new cults\\' + src}})
    rows.append((rel, src, 'Plate Accessories'))

# ---- the 16 Assault legs: Plate R / L, Buckle, Trophy R / L
for name, e in doc['legs'].items():
    rel = DIR + e['folder'].replace('/', '\\') + '\\' + name + '.stl'; f = os.path.join(LIB, side_json(rel)); d = json.load(open(f, encoding='utf-8-sig'))
    keep = [s for s in d['sockets'] if s['type'] not in ('Plate R', 'Plate L', 'Buckle', 'Trophy R', 'Trophy L')]
    WL, WR = M16(e['plates']['L']['matrix']), M16(e['plates']['R']['matrix'])
    new = [sock('Plate R', WR @ Sm @ Pc @ A, 'hip plate (mirror variant) where the B twin has it sculpted, or seated on the hip armour', 2.0),
           sock('Plate L', WL @ Pc, 'hip plate where the B twin has it sculpted, or seated on the hip armour', 2.0),
           sock('Buckle', M16(e['buckle_part']['matrix']) @ ORN, 'buckle part on the sculpted buckle (%s)' % e['buckle_part']['how'], 1.5),
           sock('Trophy R', M16(e['belt']['Belt Front R']['matrix']), 'belt rule 45 deg right of the way the buckle faces', 1.5),
           sock('Trophy L', M16(e['belt']['Belt Front L']['matrix']), 'belt rule 45 deg left of the way the buckle faces', 1.5)]
    d['sockets'] = keep + new
    write_like(rel, d, like=f)

# ---- CyberBrush tabards 1, 2, 4, 5: on the buckle's Tabard socket at 90% (exact)
for n in (1, 2, 4, 5):
    rel = CBL % n; f = os.path.join(LIB, side_json(rel)); d = json.load(open(f, encoding='utf-8-sig'))
    t = doc['buckle_part']['tabard_fits']['CyberBrush Bug Hunters - Loinclothe %d' % n]
    d['category'] = 'Tabards'; d['scale'] = 0.9
    bf = M16(d['fits']['Belt Front']); bf[:3, 3] *= 0.9; d['fits']['Belt Front'] = L(bf)        # fits are in the scaled file's coordinates
    d['fits']['Tabard'] = t['matrix']; d['exact'] = sorted(set((d.get('exact') or []) + ['Tabard'])); d['adaptor'] = BUCKLE
    d.setdefault('notes', {}).update({'Tabard': "Josh's placement under the buckle (tabard check1.blend, Nov 3), placed exactly",
        'scale': 'Josh: the CyberBrush tabards at 90% (Nov 3)', 'category': 'Tabards: hang from the buckle part (TIOW Inbox 1.17.6)',
        'adaptor': 'comes with the buckle when the legs have none yet'})
    write_like(rel, d, like=f)

# ---- CyberBrush Bug Hunters belt decorations 1-9: trophies on Trophy R / L (exact: the loop sits on the belt)
for n in range(1, 10):
    rel = CBD % n; f = os.path.join(LIB, side_json(rel)); d = json.load(open(f, encoding='utf-8-sig'))
    t = doc['trophy_fits']['CyberBrush Bug Hunters - Belt Decoration %d' % n]
    d['category'] = 'Trophies'; d.setdefault('fits', {}).update({'Trophy R': t, 'Trophy L': t}); d['exact'] = ['Trophy L', 'Trophy R']
    d.setdefault('notes', {}).update({'Trophy R': 'loop at the top on the trophy spot, face out, hanging (Josh checked, Nov 3)', 'Trophy L': 'as Trophy R',
                                      'category': 'Trophies: either side of the buckle on the belt'})
    write_like(rel, d, like=f)

with open(os.path.join(OUT, '_sources_rows.csv'), 'w', encoding='utf-8', newline='') as fh:
    for r, s, t in rows: fh.write('%s,%s,%s,\r\n' % (r, s, t))
print('written under', OUT)
