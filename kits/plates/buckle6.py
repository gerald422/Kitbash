exec(open('buckle4.py').read().split('Pref, Mref =')[0])
final = pickle.load(open('buckle_final.pkl', 'rb')); J = dict(jobs)
def facing(path, A, rad=1.6):
    sc = json.load(open(path + '.sockets.json')); M = S_WAIST @ M16(sc['fits']['Waist'])
    V, T = load(path + '.stl'); P, N = belt.surf_n(V, T, 400000)
    k = (np.linalg.norm(P - A[:3, 3], axis=1) < rad) & (N @ A[:3, 2] > 0.3); n = N[k].mean(0); return n / np.linalg.norm(n), k.sum()
for a in J:
    n, c = facing(J[a], final[a]); print('%-5s anchor Z vs buckle face normal: %.1f deg (%d pts)' % (a, np.degrees(np.arccos(np.clip(n @ final[a][:3, 2], -1, 1))), c))
