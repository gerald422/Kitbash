"""What in D:\\new cults isn't in the Kitbash Library, for the makers already in it (Nov 6). Reads only.
Buckets each file: presupported, duplicate of a library source (same bytes), mirror copy of a library part
(the L/R twin is in), OBJ beside an STL, then a rough part type from the name/folder. Writes notin_by_maker.json."""
import os, csv, json, collections, re, hashlib
H = os.path.expanduser('~/mnt/d/'); NC = H + 'new cults/'; L = H + 'Kitbash Library/'; OUT = L + '_backups/nofit-survey-2026-11-06/'
rows = list(csv.reader(open(L + '_sources.csv', encoding='utf-8-sig')))[1:]
src = {r[1].replace('\\', '/').lower(): r for r in rows if len(r) > 1}
MAKER = {'Marta': 'Marta', 'All Mar All the time': 'Mar Fil', 'BackPackUpdate-1': 'Mar Fil', 'Turtle Ninja': 'Turtle Ninja', 'Springles': 'Springles',
         'BBoosty': 'BBoosty', 'CyberBrush': 'CyberBrush', 'Old_style_space_knight_torso': 'Old Style', '_Iron Hands (3)': 'Iron Hands (3)',
         'Warhammer Techmarine Conversion Kit': 'Techmarine Conversion Kit'}
def shash(p, size):
    h = hashlib.md5(str(size).encode())
    with open(p, 'rb') as f:
        for o in (0, size // 2, max(0, size - 65536)): f.seek(o); h.update(f.read(65536))
    return h.hexdigest()
bysize = collections.defaultdict(list)
for k in src:
    p = NC + k
    # _sources keeps the maker's case; find the real path case-insensitively only when needed
    if os.path.exists(NC + src[k][1].replace('\\', '/')): p = NC + src[k][1].replace('\\', '/')
    try: bysize[os.path.getsize(p)].append(p)
    except OSError: pass
SIDE = [(r'(^|[^a-z])l([^a-z]|$)', 'r'), (r'left', 'right'), (r'(^|[^a-z])r([^a-z]|$)', 'l'), (r'right', 'left')]
srcnames = set(os.path.basename(k)[:-4] for k in src)
def twin(rel):
    n = os.path.basename(rel)[:-4].lower()
    for a, b in (('_l', '_r'), ('-l', '-r'), (' l', ' r'), ('_r', '_l'), ('-r', '-l'), (' r', ' l'), ('left', 'right'), ('right', 'left'), ('l_', 'r_'), ('r_', 'l_')):
        for m in re.finditer(re.escape(a), n):
            t = n[:m.start()] + b + n[m.end():]
            if t in srcnames: return True
    return False
PRES = re.compile(r'presup|pre-sup|pre_sup|pre sup|supported|zsup|(^|[^a-z])pres_|lychee|chitu|(^|/)sup(ports?)?(/|_|\s)|_sup\.|supp\b', re.I)
TYPES = [('Bases', r'base|terrain|scenic|diorama'), ('Arms', r'(^|[^a-z])arms?([^a-z]|$)|shoulder.?joint'), ('Legs', r'legs?([^a-z]|$)|feet|foot'),
         ('Heads', r'head|helm|face'), ('Chests', r'torso|chest|body|bust'), ('Backpacks', r'pack|jump'), ('Shoulder Pads', r'pad|pauldron|shoulder'),
         ('Hands', r'hand|fist|palm|claw'), ('Shields', r'shield'), ('Weapons', r'sword|axe|hammer|mace|blade|bolt|gun|rifle|pistol|melta|plasma|flamer|spear|lance|staff|launcher|cannon|weapon|knife|maul|glaive|chain'),
         ('Whole models / poses', r'full|complete|whole|pose|merged|assembled|model|character|captain|lieutenant|sergeant'),
         ('Bits', r'bit|accessor|grenade|pouch|seal|skull|trophy|belt|cape|cloak|tabard|loin|purity|aquila|scroll|banner|icon')]
def kind(rel):
    low = rel.lower(); n = os.path.basename(low)
    for t, rx in TYPES:
        if re.search(rx, n): return t
    for t, rx in TYPES:
        if re.search(rx, os.path.dirname(low)): return t
    return 'Unsorted'
res = collections.defaultdict(lambda: collections.defaultdict(list))
stls = set()
for top in MAKER:
    for dp, dn, fn in os.walk(NC + top):
        for f in fn:
            if f.lower().endswith('.stl'): stls.add(os.path.relpath(os.path.join(dp, f), NC).replace(os.sep, '/').lower()[:-4])
for top, mk in MAKER.items():
    for dp, dn, fn in os.walk(NC + top):
        for f in fn:
            if not f.lower().endswith(('.stl', '.obj')): continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, NC).replace(os.sep, '/')
            if rel.lower() in src: continue
            if f.lower().endswith('.obj') and rel.lower()[:-4] in stls: b = 'OBJ beside its STL'
            elif PRES.search(rel): b = 'presupported'
            else:
                sz = os.path.getsize(p); b = None
                if sz in bysize:
                    h = shash(p, sz)
                    if any(shash(q, sz) == h for q in bysize[sz]): b = 'duplicate of a library source'
                if not b and twin(rel): b = 'mirror copy (twin is in)'
                if not b: b = kind(rel)
            res[mk][b].append(rel)
json.dump(res, open(OUT + 'notin_by_maker.json', 'w'), indent=0)
cols = ['presupported', 'duplicate of a library source', 'mirror copy (twin is in)', 'OBJ beside its STL']
for mk, d in res.items():
    tot = sum(len(v) for v in d.values()); rest = {k: len(v) for k, v in sorted(d.items(), key=lambda x: -len(x[1])) if k not in cols}
    print('%s: %d not in | %s | left: %s' % (mk, tot, ', '.join('%s %d' % (c.split(' ')[0], len(d.get(c, []))) for c in cols), rest))
