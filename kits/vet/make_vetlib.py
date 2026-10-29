"""Link Vet / Bladeguard files into the test library and write their sidecars (vet_partial + pads)."""
import os, glob, json, sys
LIB = '/home/claude/test/kitlib/All Mar All the time/'
RAW = '/home/claude/raw/'; UP = '/mnt/user-data/uploads/new cults/All Mar All the time/'
side = json.load(open('/home/claude/kits/vet/vet_partial.json'))['side']
for kit in ('VeteranSquad', 'VeteranBladeSquad'):
    for f in glob.glob(LIB + kit + '/**/*.sockets.json', recursive=True) + glob.glob(LIB + kit + '/**/_fits.json', recursive=True): os.remove(f)
n = 0
for base in (RAW, UP):
    for f in glob.glob(base + 'Veteran*/**/*.stl', recursive=True):
        rel = f[len(base):]; dst = LIB + rel
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.lexists(dst): os.remove(dst)
        os.symlink(f, dst); n += 1
# the Bladeguard pad folder fits already on Josh's drive (1.6)
for f in glob.glob('/home/claude/test/reallib/All Mar All the time/VeteranBladeSquad/**/_fits.json', recursive=True):
    dst = LIB + f.split('All Mar All the time/')[1]; os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w').write(open(f).read())
w = 0
for rel, d in side.items():
    p = LIB + os.path.splitext(rel)[0] + '.sockets.json'
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(d, open(p, 'w'), indent=1); w += 1
print('linked', n, 'sidecars', w)
