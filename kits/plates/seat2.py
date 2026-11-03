exec(open('seat.py').read().split('rel = {s:')[0].replace("print('contact points", "0 and print('contact points"))
rel = {s: {a: np.linalg.inv(L[a][3]['Hip ' + s]) @ mp['res'][(a, s)]['W'] for a in jl} for s in 'RL'}
def score(W, S, N, tree, C):
    X = tf(C, W); d, j = tree.query(X); sd = ((X - S[j]) * N[j]).sum(1)
    Xa = tf(PW[::4], W); da, ja = tree.query(Xa); pen = (((Xa - S[ja]) * N[ja]).sum(1) < -0.3) & (da < 2)
    return np.median(np.abs(sd)) + 5 * pen.mean(), np.median(np.abs(sd)), pen.mean()
res = {}
for s in 'RL':
    e = []
    for a in jl:
        S, N, tree, hp = L[a]; Wt = mp['res'][(a, s)]['W']
        C = PW[(cnt[s] - (tree.query(tf(PW, Wt))[0] < 0.25)) >= (len(jl) - 1) / 2]
        cands = []
        for b, r in rel[s].items():
            if b == a: continue
            W1 = seat(hp['Hip ' + s] @ r, S, N, tree, C, lam=0.0); cands.append((score(W1, S, N, tree, C), b, W1))
        cands.sort(key=lambda c: c[0][0]); (sc, med, pen), b, W1 = cands[0]
        e.append(err(W1, Wt)); print('  %s %s: best prior %s, contact median %.3f mm, penetrating %.1f%%, off by %.2f mm (true plate scores %.3f)' % (a, s, b, med, 100 * pen, e[-1], score(Wt, S, N, tree, C)[0]))
    print('side %s: multi-start seated median %.2f / max %.2f mm' % (s, np.median(e), max(e)))
