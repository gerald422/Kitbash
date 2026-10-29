import sys; sys.path.insert(0, '/home/claude/kits')
import geo, numpy as np, os, json, collections
from fist import side, Hof
import armcheck
def run(verbose=True):
    A = json.load(open('/home/claude/kits/armrule_res.json')); H = json.load(open(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kits/handrule_res.json'))
    arms = {rel: (sd, S) for rel, sd, S, j in armcheck.arm_items()}
    rows = []
    for arel, ar in A.items():
        sd, S = arms[arel]; Ar = np.array(ar['M'])
        for wrel, hr in H.items():
            wsd = 'L' if 'Left' in wrel else 'R'
            if wsd != sd: continue
            Hj = Hof(wrel, wsd); F = np.linalg.inv(Hj)
            Wj = S @ F; Wr = Ar @ np.linalg.inv(np.array(hr['M']))
            a = geo.ang((np.linalg.inv(Wj) @ Wr)[:3, :3])
            p = np.r_[Hj[:3, 3] - 2.5 * Hj[:3, 1], 1]; d = np.linalg.norm((Wr @ p - Wj @ p)[:3])
            rows.append((a, d, os.path.basename(arel), os.path.basename(wrel)))
    a = np.array([r[0] for r in rows]); d = np.array([r[1] for r in rows])
    print('pairs %d | weapon rotation vs Josh: median %.1f, 90%% %.1f, max %.1f deg | fist moved: median %.2f, 90%% %.2f, max %.2f mm' % (
        len(a), np.median(a), np.quantile(a, .9), a.max(), np.median(d), np.quantile(d, .9), d.max()))
    per = collections.defaultdict(list)
    for r in rows: per[r[2]].append(r[0])
    bad = {k: round(float(np.median(v)), 1) for k, v in per.items() if np.median(v) > 9}
    print('arms with median > 9 deg:', bad)
    return rows
if __name__ == '__main__': run()
