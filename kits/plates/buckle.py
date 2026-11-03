import sys, json, numpy as np, pickle
sys.path.insert(0, '/home/claude/kitbash/kits'); import belt
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
jobs = [('%dA' % n, LD % ('%dA' % n)) for n in range(1, 9)] + [('%dA L' % n, LD % ('%dA L' % n)) for n in (2, 3, 4)] + [('S%d' % n, LS % n) for n in range(1, 6)]
BF = pickle.load(open('beltfront.pkl', 'rb'))
for a, path in jobs[:1] + jobs[5:6] + jobs[9:10] + jobs[12:13]:
    sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    V, T = load(path + '.stl'); P, N = belt.surf_n(V, T, 400000); P = P @ M[:3, :3].T + M[:3, 3]; N = N @ M[:3, :3].T
    L = P - belt.AXIS; az = np.degrees(np.arctan2(L[:, 0], L[:, 1])); r = np.hypot(L[:, 0], L[:, 1])
    print('==', a, 'current Belt Front at', (M @ BF[a]['Belt Front'])[:3, 3].round(2), 'facing', (M @ BF[a]['Belt Front'])[:3, 2].round(2))
    for zc in (21.0, 22.0, 22.5, 23.0, 24.0):
        k = np.abs(L[:, 2] - (zc - belt.BELT_Z)) < 0.25
        row = []
        for b in range(-40, 41, 5):
            kk = k & (np.abs(az - b) < 2.5); row.append('%4.1f' % r[kk].max() if kk.any() else '  - ')
        print('z %.1f r by azimuth -40..40:' % zc, ' '.join(row))
