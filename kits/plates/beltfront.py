import sys, json, numpy as np, pickle
sys.path.insert(0, '/home/claude/kitbash/kits'); import belt
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
s45 = np.sqrt(0.5)
belt.geo.load = load
belt.DIRS = {'Belt Front': (0, 1, 0), 'Belt Front R': (s45, s45, 0), 'Belt Front L': (-s45, s45, 0), 'Belt Back': (0, -1, 0), 'Hip R': (1, 0, 0), 'Hip L': (-1, 0, 0)}
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
jobs = [('%dA' % n, LD % ('%dA' % n)) for n in range(1, 9)] + [('%dA L' % n, LD % ('%dA L' % n)) for n in (2, 3, 4)] + [('S%d' % n, LS % n) for n in range(1, 6)]
res = {}
for a, path in jobs:
    sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    A = belt.belt_anchors(path + '.stl', M); res[a] = A
    old = {s['type']: M16(s['matrix']) for s in sc['sockets']}
    dd = ['%s %.2f' % (t, np.linalg.norm(A[t][:3, 3] - old[t][:3, 3])) for t in ('Belt Front', 'Belt Back', 'Hip R', 'Hip L') if t in A and t in old]
    miss = [t for t in belt.DIRS if t not in A]
    print(a, 'new:', ', '.join('%s at %s' % (t, ((M @ A[t])[:3, 3]).round(1)) for t in ('Belt Front R', 'Belt Front L') if t in A), '| existing re-found within mm:', ', '.join(dd), '| missing', miss)
pickle.dump(res, open('beltfront.pkl', 'wb'))
