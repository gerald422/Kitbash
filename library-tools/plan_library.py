#!/usr/bin/env python3
"""Plan the Kitbash Library: every set-up part in D:\\new cults (a .sockets.json
beside it, or a pad in a folder with a _fits.json), de-duplicated, filed as
<Creator> - <Mark>\\<Kit>\\[groups]\\<Type>\\<file>. Writes ~/catalogue/plan.json
and plan.csv. Reads only."""
import os, sys, json, re, hashlib, time, csv, collections

SRC = os.path.expanduser('~/mnt/new cults')
# optional: --work <dir> (default ~/catalogue), --survey <file> (default ~/lib_survey.json),
# --only <top folder>[,<top folder>...] (plan just those, e.g. the creators being added)
_a = sys.argv[1:]
def _opt(name, default):
    return _a[_a.index(name) + 1] if name in _a else default
WORK = os.path.expanduser(_opt('--work', '~/catalogue'))
ONLY = set(x for x in _opt('--only', '').split(',') if x)
os.makedirs(WORK, exist_ok=True)
survey = json.load(open(os.path.expanduser(_opt('--survey', '~/lib_survey.json'))))
if ONLY:
    survey = {'side': [x for x in survey['side'] if x.split('/')[0] in ONLY],
              'fits': [x for x in survey['fits'] if x.split('/')[0] in ONLY]}

PART_TYPES = json.load(open(os.path.join(WORK, 'partTypes.json')))
STRIP = ['raw', 'rawstl', 'stl', 'mirrored', 'mirror', 'sergeant', 'support', 'supported', 'presupported']
def words(s):
    return [w for w in re.sub(r'[_\-\s]+', ' ', str(s).lower()).strip().split(' ') if w]
def norm(s):
    w = words(s)
    while len(w) > 1 and w[-1] in STRIP:
        w.pop()
    return ' '.join(w)
TYPE_OF = {}
for t, al in PART_TYPES.items():
    for a in [t] + al:
        TYPE_OF[norm(a)] = t
def folder_type(name):
    return TYPE_OF.get(norm(name))
def path_type(rel):
    for f in reversed(rel.split('/')[:-1]):
        t = folder_type(f)
        if t:
            return t
    return None
def noise(name):
    w = words(name)
    return not w or all(x in STRIP or x in ('raw stl', 'unsupported') for x in w)

PAD_NAMES = (("Knee Pads", re.compile(r"(shin|chin|knee)[ _-]?pads?|greaves?", re.I)),
             ("Shoulder Pads", re.compile(r"shoulder[ _-]?pads?|pauldrons?", re.I)))
TIOW_NAMES = {"Shin Pads": "Knee Pads", "Bodies": "Chests", "Torsos": "Chests"}
def side_words(*texts):
    ws = set()
    for t in texts:
        t = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(t or ""))
        ws |= set(re.split(r"[^a-z]+", t.lower()))
    return ws
def part_side(*texts):
    ws = side_words(*texts)
    r = bool(ws & {"r", "right", "rh"}); l = bool(ws & {"l", "left", "lh"})
    return "R" if r and not l else "L" if l and not r else None
def side_m(*texts):
    s = part_side(*texts)
    if s is None and side_words(*texts) & {"mirrored", "mirror"}:
        s = "L"
    return s

# ---------------------------------------------------------------- where
TOP = {'All Mar All the time': ('Mar Fil', 1), 'Intercessors-V2': ('Mar Fil', 0),
       'HelmetsUpdate': ('Mar Fil', 0), 'HelmetsUpdates-1': ('Mar Fil', 0),
       'BackPackUpdate-1': ('Mar Fil', 0),
       'VeteranBladeSquad-20251116T204804Z-1-001': ('Mar Fil', 0),
       'Marta': ('Marta PunkGirl', 1), 'Springles': ('Springles', 1),
       'Turtle Ninja': ('Turtle Ninja', 1), 'body adaptor': ('Bits', None),
       'BBoosty': ('BBoosty', 1), 'CyberBrush': ('CyberBrush', 1)}
PRIMARY_TOPS = {'All Mar All the time', 'Marta', 'Springles', 'Turtle Ninja', 'body adaptor', 'BBoosty', 'CyberBrush'}
KIT_ALIAS = {'helmetsupdates': 'HelmetsUpdate', 'helmetsupdate': 'HelmetsUpdate',
             'backpackupdate': 'BackPackUpdate'}
def clean(n):
    o = n
    n = re.sub(r'-\d{8}T\d{6}Z(-\d+)*', '', n)
    n = re.sub(r'(\s*\(\d+\))+$', '', n)
    n = re.sub(r"^TurtleNinja's\s+", '', n)
    n = re.sub(r'^(Marta Punkgirl - |MartaPG |Marta[_ ])', '', n, flags=re.I)
    if re.match(r'Cyberbrush_3D_Pulses_\d{4}_\d{2}_', n, re.I):
        n = n[len('Cyberbrush_3D_Pulses_2024_11_'):].replace('_', ' ')
    n = re.sub(r'\s{2,}', ' ', n).strip(' -_')
    if re.fullmatch(r'(HelmetsUpdates?|BackPackUpdate)-1', n, re.I):
        n = n[:-2]
    return KIT_ALIAS.get(n.lower(), n) or o
def clean_group(n):
    n = re.sub(r'-\d{8}T\d{6}Z(-\d+)*', '', n)
    # side / raw annotations: the side goes to a Left / Right folder of its own
    n = re.sub(r'(?i)[-_ ]*\(?(left|right)\)?(orientated)?|[-_ ]*raw[-_ ]*stl|[-_ ]*mirrored|[-_ ]+raw$', '', n)
    n = re.sub(r'(\s*\(\d+\))+$', '', n)
    return re.sub(r'\s{2,}', ' ', n).strip(' -_') or n
def fuzzy(n):
    n = re.sub(r'[^a-z0-9]', '', n.lower())
    n = re.sub(r'\d+$', '', n) if not n.isdigit() else n
    return n.rstrip('s')
def mark_of(creator, kit, top):
    k = kit.lower()
    if creator == 'Mar Fil':
        return 'Tacticus'
    if creator == 'Springles':
        return 'Heresy' if k.startswith('pattern') else 'Weapons'
    if creator == 'Turtle Ninja':
        return 'Tacticus' if 'mk10' in k else 'Heresy'
    if creator == 'BBoosty':
        return 'Heresy'
    if creator == 'CyberBrush':
        return 'Tacticus'
    if creator == 'Marta PunkGirl':
        if re.search(r'termin|temminator', k): return 'Terminator'
        if re.search(r'phobo|eliminator', k): return 'Phobos'
        if re.search(r'aggressor|heavy|thicc|gravis|inceptor', k): return 'Gravis'
        if re.search(r'weapon', k): return 'Weapons'
        return 'Tacticus'
    return None

# ---------------------------------------------------------------- parts
def find_stl(d, stem):
    for e in ('.stl', '.STL', '.Stl'):
        p = os.path.join(d, stem + e)
        if os.path.isfile(p):
            return p
    return None

parts = {}          # rel stl path -> record
for rel_sc in survey['side']:
    d, f = os.path.split(rel_sc)
    stem = f[:-len('.sockets.json')]
    stl = find_stl(os.path.join(SRC, d), stem)
    if not stl:
        print('NO STL', rel_sc); continue
    rel = os.path.relpath(stl, SRC).replace(os.sep, '/')
    try:
        side = json.load(open(os.path.join(SRC, rel_sc), encoding='utf-8'))
    except Exception as e:
        print('BAD SIDECAR', rel_sc, e); continue
    parts[rel] = {'rel': rel, 'sidecar': rel_sc, 'side': side, 'folderFits': {}}

for d in survey['fits']:
    fits = json.load(open(os.path.join(SRC, d, '_fits.json'), encoding='utf-8'))
    fits = {k: v for k, v in fits.items() if not k.startswith('_')}
    for f in sorted(os.listdir(os.path.join(SRC, d))):
        if not f.lower().endswith('.stl'):
            continue
        rel = d + '/' + f
        stem = f[:-4]
        rec = parts.get(rel)
        cat = (rec['side'].get('category') if rec else None)
        if not cat:
            cat = next((c for c, rx in PAD_NAMES if rx.search(stem)), None) or path_type(rel)
        base = {'Knee Pads': 'Shin', 'Shoulder Pads': 'Pad'}.get(cat)
        use = {k: v for k, v in fits.items() if base and k.split(' ')[0] == base}
        if not use:
            continue
        if rec is None:
            rec = parts[rel] = {'rel': rel, 'sidecar': None, 'side': {}, 'folderFits': {}}
        rec['folderFits'].update(use)

print('parts', len(parts))

# ---------------------------------------------------------------- category
for rel, r in parts.items():
    stem = os.path.splitext(os.path.basename(rel))[0]
    c = r['side'].get('category')
    how = 'sidecar'
    if not (isinstance(c, str) and c.strip()):
        c = next((cc for cc, rx in PAD_NAMES if rx.search(stem)), None); how = 'pad name'
        if not c:
            c = path_type(rel); how = 'folder'
        if not c:
            c = 'Unsorted'; how = 'none'
    r['category'] = TIOW_NAMES.get(c.strip(), c.strip()); r['catFrom'] = how

# ---------------------------------------------------------------- size + mtime
t0 = time.time()
for rel, r in parts.items():
    st = os.stat(os.path.join(SRC, rel))
    r['bytes'] = st.st_size
    r['scMtime'] = os.stat(os.path.join(SRC, r['sidecar'])).st_mtime if r['sidecar'] else 0
print('stat %.1fs' % (time.time() - t0))

# ---------------------------------------------------------------- duplicates (sampled hash in same-size groups)
HC = os.path.join(WORK, 'hash_cache.json')
cache = json.load(open(HC)) if os.path.exists(HC) else {}
def shash(rel, size):
    k = '%s|%d' % (rel, size)
    if k in cache:
        return cache[k]
    h = hashlib.md5(str(size).encode())
    with open(os.path.join(SRC, rel), 'rb') as fh:
        for off in (0, max(0, size // 2 - 131072), max(0, size - 262144)):
            fh.seek(off); h.update(fh.read(262144))
    cache[k] = h.hexdigest()
    return cache[k]
bysize = collections.defaultdict(list)
for rel, r in parts.items():
    bysize[r['bytes']].append(rel)
n = 0
for size, rels in bysize.items():
    if len(rels) > 1:
        for rel in rels:
            parts[rel]['hash'] = shash(rel, size); n += 1
json.dump(cache, open(HC, 'w'))
print('hashed', n, '%.1fs' % (time.time() - t0))
groups = collections.defaultdict(list)
for rel, r in parts.items():
    groups[r.get('hash') or ('u:' + rel)].append(rel)

def rank(rel, same):
    r = parts[rel]
    top = rel.split('/')[0]
    segs = rel.split('/')
    ki = TOP[top][1]
    kit = clean(segs[ki]) if ki is not None and ki < len(segs) - 1 else clean(top)
    upd = 'update' in kit.lower()   # its own update kit (HelmetsUpdate, BackPackUpdate)
    if same:   # identical sidecars: file it in its own update kit, else where it ships
        return (upd, top in PRIMARY_TOPS, len(r['folderFits']), -len(rel))
    return (top in PRIMARY_TOPS, r['sidecar'] is not None, r['scMtime'], len(r['folderFits']), -len(rel))
dupes = []
for h, rels in groups.items():
    if len(rels) < 2:
        continue
    same_all = len({json.dumps(parts[x]['side'].get(k), sort_keys=True) for x in rels for k in ('fits',)}) == 1 and \
        len({json.dumps({k: v for k, v in parts[x]['side'].items() if k not in ('part', 'sockets')}, sort_keys=True) for x in rels}) == 1
    rels.sort(key=lambda x: rank(x, same_all), reverse=True)
    keep = parts[rels[0]]
    for o in rels[1:]:
        r = parts[o]
        same = json.dumps(r['side'], sort_keys=True) == json.dumps(keep['side'], sort_keys=True)
        r['dupOf'] = rels[0]
        # a dropped copy's folder fits still count when the keeper has none for that joint
        for k, v in r['folderFits'].items():
            keep['folderFits'].setdefault(k, v)
        dupes.append((o, rels[0], same))

# ---------------------------------------------------------------- destination
plan = []
for rel, r in sorted(parts.items()):
    if r.get('dupOf'):
        continue
    segs = rel.split('/')
    top = segs[0]
    creator, ki = TOP[top]
    fname = segs[-1]; stem = os.path.splitext(fname)[0]
    cat = r['category']
    if creator == 'Bits':
        kit, mid = None, []
        topdir = 'Bits'
    else:
        kit = clean(segs[ki]) if ki < len(segs) - 1 else clean(top)
        mid = segs[ki + 1:-1]
        topdir = '%s - %s' % (creator, mark_of(creator, kit, top))
    full, lean = [], []
    seen_exact = {kit.lower() if kit else ''}
    seen_fuzzy = {fuzzy(kit) if kit else ''}
    for m in mid:
        c = clean_group(m)
        if noise(c):
            continue
        if c.lower() not in seen_exact:
            full.append(c)
        if fuzzy(c) not in seen_fuzzy and folder_type(c) != cat:
            lean.append(c)
        seen_exact.add(c.lower()); seen_fuzzy.add(fuzzy(c))
    # side carried by the original folder only (LeftOrientated, ...-Mirrored)
    parent = segs[-2]
    tfold = cat
    sf = None
    if part_side(stem) is None and part_side(stem, parent) is not None:
        sf = 'named:' + part_side(stem, parent)
    elif side_m(stem) is None and side_m(stem, parent) is not None:
        sf = 'mirrored'
    r['sideFromFolder'] = sf
    # the add-on reads a side from the folder the file sits in: keep it in a
    # Left / Right / Mirrored folder under the type folder (TIOW skips it)
    sub = {'named:L': 'Left', 'named:R': 'Right', 'mirrored': 'Mirrored'}.get(sf)
    tfold = cat + ('/' + sub if sub else '')
    r['_full'] = full; r['_lean'] = lean; r['_top'] = topdir; r['_kit'] = kit; r['_tfold'] = tfold
    dst = '/'.join([topdir] + ([kit] if kit else []) + lean + [tfold, fname])
    r['dst'] = dst
    plan.append(r)

# collisions: same target (case-insensitive) -> keep the full group path for those
def coll():
    c = collections.defaultdict(list)
    for r in plan:
        c[r['dst'].lower()].append(r)
    return {k: v for k, v in c.items() if len(v) > 1}
cl = coll()
for k, rs in cl.items():
    for r in rs:
        r['dst'] = '/'.join([r['_top']] + ([r['_kit']] if r['_kit'] else []) + r['_full'] + [r['_tfold'], os.path.basename(r['rel'])])
        r['note'] = 'collision: kept the folder names'
cl2 = coll()
for k, rs in cl2.items():
    for i, r in enumerate(rs):
        segs = r['rel'].split('/')
        r['dst'] = os.path.dirname(r['dst']) + '/' + os.path.splitext(segs[-1])[0] + ' (%s)' % clean_group(segs[-2]) + os.path.splitext(segs[-1])[1]
        r['note'] = 'collision: renamed'
cl3 = coll()

# ---------------------------------------------------------------- report
for r in plan:
    r['scDst'] = os.path.splitext(r['dst'])[0] + '.sockets.json'
with open(os.path.join(WORK, 'plan.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['library path', 'source', 'type', 'type from', 'MB', 'folder fits', 'side from folder', 'note'])
    for r in plan:
        w.writerow([r['dst'].replace('/', '\\'), r['rel'].replace('/', '\\'), r['category'], r['catFrom'],
                    round(r['bytes'] / 1e6, 1), ' '.join(sorted(r['folderFits'])), r.get('sideFromFolder') or '', r.get('note', '')])
with open(os.path.join(WORK, 'dupes.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['dropped copy', 'kept', 'same sidecar'])
    for o, k, s in dupes:
        w.writerow([o.replace('/', '\\'), k.replace('/', '\\'), s])
json.dump([{k: v for k, v in r.items() if not k.startswith('_')} for r in plan],
          open(os.path.join(WORK, 'plan.json'), 'w'))

print('planned', len(plan), 'dropped copies', len(dupes), 'differing sidecars', sum(1 for d in dupes if not d[2]))
print('GB %.2f' % (sum(r['bytes'] for r in plan) / 1e9))
print('collisions', len(cl), '->', len(cl2), '->', len(cl3))
print('type from', collections.Counter(r['catFrom'] for r in plan))
print('side from folder', collections.Counter(r['sideFromFolder'] for r in plan))
print('longest path', max(len(r['scDst']) for r in plan) + len('D:\\Kitbash Library\\'))
print('support in path', sum(1 for r in plan if 'support' in r['rel'].lower()))
c = collections.Counter(r['dst'].split('/')[0] for r in plan)
for k, v in sorted(c.items()): print('  ', v, k)
c = collections.Counter('/'.join(r['dst'].split('/')[:2]) for r in plan)
for k, v in sorted(c.items()): print('    ', v, k)
