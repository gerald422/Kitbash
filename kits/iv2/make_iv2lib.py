"""Link the staged Intercessors V2 files into the test library (kitlib = D:\\new cults) and write their sidecars."""
import os, glob, json
LIB = '/home/claude/test/kitlib/'; NC = '/mnt/user-data/uploads/new cults/'
KIT = 'Intercessors-V2/'
for f in glob.glob(LIB + KIT + '**/*.sockets.json', recursive=True): os.remove(f)
n = 0
for f in glob.glob(NC + KIT + '**/*.stl', recursive=True):
    dst = LIB + f[len(NC):]; os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.lexists(dst): os.remove(dst)
    os.symlink(f, dst); n += 1
side = json.load(open('/home/claude/kits/iv2/iv2_partial.json'))['side']
w = 0
for rel, d in side.items():
    p = LIB + os.path.splitext(rel)[0] + '.sockets.json'; os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, 'w'), indent=1); w += 1
print('linked', n, 'sidecars', w)
