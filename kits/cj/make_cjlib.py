"""Link the staged Chaplain with Jump Pack files into the test library (kitlib = D:\\new cults) and write their sidecars."""
import os, glob, json
LIB = '/home/claude/test/kitlib/'; NC = '/mnt/user-data/uploads/new cults/'
KIT = 'All Mar All the time/ChaplainWithJumpPack (1)/'
for f in glob.glob(LIB + KIT + '**/*.sockets.json', recursive=True): os.remove(f)
n = 0
for f in glob.glob(NC + KIT + '**/*.stl', recursive=True):
    dst = LIB + f[len(NC):]; os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.lexists(dst): os.remove(dst)
    os.symlink(f, dst); n += 1
side = json.load(open('/home/claude/kits/cj/cj_partial.json'))['side']
w = 0
for rel, d in side.items():
    p = LIB + 'All Mar All the time/' + os.path.splitext(rel)[0] + '.sockets.json'; os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, 'w'), indent=1); w += 1
print('linked', n, 'sidecars', w)
