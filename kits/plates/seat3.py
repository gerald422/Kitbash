exec(open('seat2.py').read().split('res = {}')[0])
LS = '/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Legs/MarFil Assault - Legs %s'
for n in range(1, 6):
    a = 'S%d' % n; VA, TA = load(LS % n + '.stl'); S, N = sampn(VA, TA); tree = cKDTree(S); hp = hips(LS % n)
    for s in 'RL':
        C = CP[s]; cands = []
        for b, r in rel[s].items():
            W1 = seat(hp['Hip ' + s] @ r, S, N, tree, C, lam=0.0); cands.append((score(W1, S, N, tree, C), b, W1))
        cands.sort(key=lambda c: c[0][0]); (sc, med, pen), b, W1 = cands[0]
        spread = max(err(W1, c[2]) for c in cands[:3])
        mp['res'][(a, s)] = dict(W=W1, med=med, p95=None, mirror=False, seated_from=b)
        print('standing legs %d %s: seated from %s, contact median %.3f mm, penetrating %.1f%%, next-best seats within %.2f mm' % (n, s, b, med, 100 * pen, spread))
pickle.dump(mp, open('mfplate.pkl', 'wb'))
