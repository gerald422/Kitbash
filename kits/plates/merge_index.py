"""Merge the plates/buckle delivery into the PC's _builder/index.json in place (no Prepare needed):
existing parts take their new sidecar fields (fits, sockets, type, exact, adaptor, scale, variants); the CyberBrush
tabards also take their new 90% previews; new parts come in whole with their previews.
python merge_index.py PC_INDEX TEST_LIB OUT_DIR"""
import json, os, sys, shutil
pc, tlib, out = sys.argv[1:4]
raw = open(pc, 'rb').read(); d = json.loads(raw)
assert json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode('utf-8') == raw
T = {e['path']: e for e in json.load(open(os.path.join(tlib, '_builder', 'index.json')))['parts']}
byp = {e['path']: i for i, e in enumerate(d['parts'])}
KEEP = ('id', 'path', 'anchored', 'prev', 'tris')
newprev, upd, add = [], [], []
for path, e in T.items():
    if path not in byp:
        if 'Torso 1' in path: continue
        d['parts'].append(e); newprev.append(e['prev']); add.append(e['name']); continue
    old = d['parts'][byp[path]]; ne = {k: old[k] for k in KEEP if k in old}
    for k, v in e.items():
        if k not in KEEP: ne[k] = v
    if e.get('scale') and e.get('scale') != old.get('scale'):      # a new scale: the new preview (scale applied)
        ne['prev'], ne['tris'] = e['prev'], e['tris']; newprev.append(e['prev'])
    keys = list(old.keys()) + [k for k in ne if k not in old]
    ne = {k: ne[k] for k in keys if k in ne}
    if ne != old: upd.append(e['name'])
    d['parts'][byp[path]] = ne
os.makedirs(os.path.join(out, 'previews'), exist_ok=True)
for p in newprev: shutil.copyfile(os.path.join(tlib, '_builder', p), os.path.join(out, p))
open(os.path.join(out, 'index.json'), 'wb').write(json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode('utf-8'))
print('updated %d: %s\nadded %d: %s\npreviews %d' % (len(upd), ', '.join(sorted(upd)), len(add), ', '.join(sorted(add)), len(newprev)))
