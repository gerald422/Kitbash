import sys, json, numpy as np, pickle
sys.path.insert(0, '/home/claude/kitbash/kits'); import belt
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
belt.geo.load = load
BS = pickle.load(open('buckle_sockets.pkl', 'rb')); BF = pickle.load(open('beltfront.pkl', 'rb'))
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
jobs = [('%dA' % n, LD % ('%dA' % n)) for n in range(1, 9)] + [('%dA L' % n, LD % ('%dA L' % n)) for n in (2, 3, 4)] + [('S%d' % n, LS % n) for n in range(1, 6)]
TR = {}
for a, path in jobs:
    sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    z = (M @ BS['pose'][a] @ BS['ORN'])[:3, 2]; az = np.arctan2(z[0], z[1])          # buckle facing, from front (+ = model right)
    belt.DIRS = {'Belt Front R': (np.sin(az + np.pi / 4), np.cos(az + np.pi / 4), 0), 'Belt Front L': (np.sin(az - np.pi / 4), np.cos(az - np.pi / 4), 0)}
    A = belt.belt_anchors(path + '.stl', M); TR[a] = A
    mv = [np.linalg.norm((M @ A[t])[:3, 3] - (M @ BF[a][t])[:3, 3]) for t in A]
    print('%-5s buckle faces %5.1f deg; trophy spots moved %.2f / %.2f mm from the torso-front ones' % (a, np.degrees(az), *mv))
pickle.dump(TR, open('trophy_spots.pkl', 'wb'))
