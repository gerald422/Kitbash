"""File the leftovers in kits already set up (Mar Fil, TN, Springles, BBoosty, Marta) without fits, so nothing is
missed (Josh, Nov 6: every type; posed/whole models and bases stay out but are logged). Reads leftovers.json
(survey.py). Writes plan_all.json (rel -> category, note) and log_all.csv (every leftover: filed or why not).
--write writes the sidecars beside the sources in D:\\new cults (never over an existing one)."""
import os, csv, json, re, sys, collections
import numpy as np
H = os.path.expanduser('~/mnt/d/'); NC = H + 'new cults/'; L = H + 'Kitbash Library/'; OUT = L + '_backups/nofit-survey-2026-11-06/'
MAKERS = {'Mar Fil', 'Turtle Ninja', 'Springles', 'BBoosty', 'Marta'}
rows = list(csv.reader(open(L + '_sources.csv', encoding='utf-8-sig')))[1:]
PT = json.load(open(OUT + 'partTypes.json'))
def words(s): return [w for w in re.sub(r'[_\-\s]+', ' ', str(s).lower()).strip().split(' ') if w]
TYPE_OF = {' '.join(words(a)): t for t, al in PT.items() for a in [t] + al}
TYPE_OF.update({'bodies': 'Chests', 'torsos': 'Chests', 'shin pads': 'Knee Pads'})
def path_type(rel):
    for f in reversed(rel.split('/')[:-1]):
        t = TYPE_OF.get(' '.join(words(f)))
        if t: return t
sib = collections.defaultdict(collections.Counter)
for r in rows:
    if len(r) > 2: sib[os.path.dirname(r[1].replace('\\', '/')).lower()][r[2]] += 1
# folded maker's left copies: variant 'from' keeps the library path the copy had (maker's file name)
folded = {}
for r in rows:
    try: d = json.load(open(L + r[0].replace('\\', '/')[:-4] + '.sockets.json', encoding='utf-8'))
    except Exception: continue
    for v in d.get('variants') or []:
        fr = str(v.get('from') or '')
        if fr.lower().endswith('.stl'): folded[(r[1].split('\\')[0].lower(), os.path.basename(fr.replace('\\', '/')).lower())] = r[0]
def ntri(p):
    with open(p, 'rb') as f: h = f.read(84)
    if h[:5].lower() == b'solid':
        t = open(p, 'rb').read()
        if b'facet' in t[:1000]: return t.count(b'facet normal'), 'a'
    return int.from_bytes(h[80:84], 'little'), 'b'
import time, atexit
T0 = time.time(); CF = os.path.expanduser('~/lw5/ext_cache.json')
_EXT = json.load(open(CF)) if os.path.exists(CF) else {}
def _save(): json.dump(_EXT, open(CF, 'w'))
def ext(p):
    if p in _EXT: return np.array(_EXT[p])
    if time.time() - T0 > 140: _save(); print('BUDGET - run again', len(_EXT)); os._exit(3)
    r = _ext(p); _EXT[p] = [float(x) for x in r]; return r
def _ext(p):
    n, k = ntri(p)
    if k == 'a': v = np.array(re.findall(rb'vertex\s+(\S+)\s+(\S+)\s+(\S+)', open(p, 'rb').read()), float)
    else: v = np.fromfile(p, dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]), count=n, offset=84)['v'].reshape(-1, 3)
    return np.sort(v.max(0) - v.min(0))
libtri = collections.defaultdict(list)
for r in rows:
    p = L + r[0].replace('\\', '/')
    try: libtri[(r[1].split('\\')[0].lower(), ntri(p)[0])].append(p)
    except OSError: pass
VALID = (set(r[2] for r in rows if len(r) > 2) | set(PT)) - {' pipes'}
def body_name(n):
    if re.search(r'armou?r', n): return 'Unsorted'
    if re.search(r'(^|[^a-z])wings?([^a-z]|$)', n): return 'Wings'
    if re.search(r'(^|[^a-z])bike([^a-z]|$)', n): return 'Bikes' if n.strip('_ 0123456789') == 'bike' else 'Bike Parts'
    for c in ('Shoulder Pads', 'Knee Pads', 'Cloaks', 'Tabards', 'Loincloths', 'Heads', 'Jump Packs', 'Backpacks', 'Chests', 'Legs', 'Arms', 'Shields'):
        if cat_by_name(n, '') == c: return c
def cat_by_name(n, rel):
    if re.search(r'shoulder.?pad|sholder.?pad|pauldron', n): return 'Shoulder Pads'
    if re.search(r'shin.?pad|knee.?pad|greave', n): return 'Knee Pads'
    if re.search(r'cloak|cape', n): return 'Cloaks'
    if re.search(r'tabard', n): return 'Tabards'
    if re.search(r'loin', n): return 'Loincloths'
    if re.search(r'helm|head|mask|face', n): return 'Heads'
    if re.search(r'jump.?pack|jet.?pack|thruster', n): return 'Jump Packs'
    if re.search(r'back.?pack|power.?pack|powerpack', n): return 'Backpacks'
    if re.search(r'torso|chest|body|upper', n): return 'Chests'
    if re.search(r'(^|[^a-z])legs?([^a-z]|$)|feet|foot', n): return 'Legs'
    if re.search(r'(^|[^a-z])(arms?|amrs)([^a-z]|$)|arm\d|\d+arm', n): return 'Arms'
    if re.search(r'shield', n): return 'Shields'
    if re.search(r'hand|palm', n) and re.search(r'pistol|revolver|bolter|rifle|gun|melta|plasma|flamer|shotgun|carbine|volkite|shredder', n): return 'Pistols'
    if re.search(r'hand|palm', n) and re.search(r'sword|axe|hammer|mace|blade|maul|glaive|spear|knife|crozius|halberd|staff|trident|scythe|flail', n): return 'Melee'
    if re.search(r'hand|fist|palm|claw|gauntlet|glove', n): return 'Hands'
    if re.search(r'grenade|pouch|holster|sheat|relic|accessor|(^|[^a-z])acc([^a-z]|$)|seal|skull|trophy|scroll|auspex|case|bayonet|purity|book|vial|chain$', n): return 'Accessories'
    if re.search(r'heavy.?bolter|cannon|multi.?melta|lascannon|rocket|launcher|missile', n): return 'Heavy Weapons'
    if re.search(r'pistol|revolver|sword|axe|hammer|mace|blade|maul|glaive|spear|knife|crozius|halberd|staff|trident|scythe|bolter|rifle|gun|melta|plasma|flamer|shotgun|carbine|volkite|weapon', n): return 'Hand-less Weapons'
    return None
JUNK_SKIP = re.compile(r'(^|/)\._')
WHOLE = re.compile(r'(^|[^a-z])(pose\s*\d|full|assembled|complete|whole|wargearless)([^a-z]|$)|^pose\d|_comp($|_)', re.I)
BASE = re.compile(r'(^|[^a-z])(base|bases|rock|rocks|terrain|scenic|diorama)([^a-z]|$)|\d+mm', re.I)
HIDE = re.compile(r'aquil|purity|seal|scroll|parchment', re.I)
left = json.load(open(OUT + 'leftovers.json'))
plan, log, hide = {}, [], []
seen = collections.defaultdict(list)
for i, (mk, rel, bucket, ft) in enumerate(left):
    if i % 200 == 0: print('progress', i, round(time.time() - T0), flush=True)
    if mk not in MAKERS: continue
    n = os.path.basename(rel)[:-4]; low = n.lower(); top = rel.split('/')[0].lower(); d = os.path.dirname(rel).lower()
    def S(why): log.append((mk, rel, 'left out', why))
    if JUNK_SKIP.search(rel): S('macOS "._" resource file, not a mesh'); continue
    if rel.lower().endswith('.obj'): S('OBJ (no STL beside it) - convert when wanted'); continue
    if (top, os.path.basename(rel).lower()) in folded: S('maker\'s left copy, folded into %s as its mirror' % folded[(top, os.path.basename(rel).lower())].split('\\')[-1][:-4]); continue
    if os.path.exists(NC + rel[:-4] + '.sockets.json'): S('already has a sidecar (not in the library: check)'); continue
    try: t = ntri(NC + rel)[0]
    except Exception as e: S('unreadable: %s' % e); continue
    same = None
    cands = libtri.get((top, t), [])
    if cands:
        e = ext(NC + rel)
        for q in cands:
            try:
                if np.abs(ext(q) - e).max() < 0.02: same = q; break
            except Exception: pass
    if same: S('same shape as library part %s (a mirror or re-export)' % os.path.basename(same)[:-4]); continue
    sc = sib.get(d); dn = os.path.basename(os.path.dirname(rel)).lower()
    hl = re.search(r'no.?hands?|without.?hands?|handless|hand.?less|separated', low)
    if hl: cat, how = 'Hand-less Weapons', 'name says no hand'
    elif mk == 'Springles' and re.search(r'belt \d', low): cat, how = 'Heavy Weapon Cables', 'name (ammo belt)'
    elif BASE.search(low): S('base, rock or scenery'); continue
    else:
        cat = body_name(low); how = 'file name'
        if not cat:
            if mk != 'Springles' and (WHOLE.search(low) or WHOLE.search(dn)): S('posed or whole model'); continue
            if sc: cat, how = sc.most_common(1)[0][0], 'same folder as %d library parts (%s)' % (sum(sc.values()), sc.most_common(1)[0][0])
            else:
                cat = path_type(rel); how = 'folder name'
                if not cat and BASE.search(dn): S('base, rock or scenery'); continue
                if not cat: cat = cat_by_name(low, rel); how = 'file name'
        if not cat: cat, how = 'Unsorted', 'no type found'
    if cat not in VALID: how += ' (%s is not a part type)' % cat; cat = 'Unsorted'
    if cat == 'Bases': S('base (bases stay out for now)'); continue
    note = 'filed without a fit so it is not missed (Nov 6, Josh): type from the %s; no fit yet' % how
    plan[rel] = {'category': cat, 'note': note, 'maker': mk}
    log.append((mk, rel, 'filed', cat + ' - ' + how))
    if HIDE.search(low): hide.append(rel)
_save()
json.dump(plan, open(OUT + 'plan_all.json', 'w'), indent=0)
with open(OUT + 'log_all.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, lineterminator='\r\n'); w.writerow(['maker', 'source (D:\\new cults)', 'result', 'type or why']); w.writerows(sorted(log))
json.dump(hide, open(OUT + 'hide_by_name.json', 'w'), indent=0)
for mk in sorted(MAKERS):
    f = collections.Counter(v['category'] for v in plan.values() if v['maker'] == mk)
    s = collections.Counter(re.sub(r' (as its mirror|as library part).*|library part .*', '', x[3]) for x in log if x[0] == mk and x[2] == 'left out')
    print('== %s: filed %d %s\n   left out %d %s' % (mk, sum(f.values()), dict(f.most_common()), sum(s.values()), dict(s.most_common())))
print('aquila/seal/scroll by name:', len(hide))
if '--write' in sys.argv:
    k = 0
    for rel, v in plan.items():
        p = NC + rel[:-4] + '.sockets.json'
        if os.path.exists(p): continue
        json.dump({'schemaVersion': 1, 'part': os.path.basename(rel)[:-4], 'category': v['category'], 'sockets': [], 'fits': {},
                   'notes': {'category': v['note']}}, open(p, 'w', encoding='utf-8'), indent=1); k += 1
    print('sidecars written', k)
