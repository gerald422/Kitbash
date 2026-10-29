"""Test library: raw STLs linked, plus the sidecars built for the kit (merged with what's already on Josh's drive)."""
import os, json, glob, shutil, sys
LIB = '/home/claude/test/kitlib/All Mar All the time/'
RAW = '/home/claude/raw/'; UP = '/mnt/user-data/uploads/new cults/All Mar All the time/'
OLD = '/home/claude/test/reallib/All Mar All the time/'
side = json.load(open(sys.argv[1]))['side']
if os.path.exists('/home/claude/test/kitlib'): shutil.rmtree('/home/claude/test/kitlib')
n = 0
for base in (RAW, UP):
    for f in glob.glob(base + 'AssaultMarines-V2/**/*.stl', recursive=True):
        rel = f[len(base):]; dst = LIB + rel
        if os.path.exists(dst): continue
        os.makedirs(os.path.dirname(dst), exist_ok=True); os.symlink(f, dst); n += 1
for f in glob.glob(OLD + 'AssaultMarines-V2/**/_fits.json', recursive=True) + glob.glob(OLD + 'AssaultMarines-V2/**/ShoulderPads/*.sockets.json', recursive=True):
    dst = LIB + f[len(OLD):]; os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy(f, dst)
def merge(mine, theirs):
    out = dict(theirs); out.update({k: v for k, v in mine.items() if k not in ('sockets', 'fits')})
    types = {s['type'] for s in mine['sockets']}
    out['sockets'] = [s for s in theirs.get('sockets', []) if s.get('type') not in types] + mine['sockets']
    out['fits'] = dict(theirs.get('fits') or {}); out['fits'].update(mine['fits'])
    return out
w = 0
for rel, d in side.items():
    p = LIB + os.path.splitext(rel)[0] + '.sockets.json'
    dev = UP + os.path.splitext(rel)[0] + '.sockets.json'
    if os.path.exists(dev): d = merge(d, json.load(open(dev)))
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(d, open(p, 'w'), indent=1); w += 1
print('linked', n, 'sidecars', w)
