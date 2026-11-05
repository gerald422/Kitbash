import sys, json, numpy as np
sys.path.insert(0, '/home/claude/real'); import fitlib as F
from reg import sicp, rots24
U = '/mnt/user-data/uploads/d/'
CAP = U + 'Kitbash Library/_backups/vitalykhan-captain-2026-11-02/objects/'
MF = U + 'Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1.stl'
sk = json.load(open('/home/claude/kitbash/library/Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1.sockets.json'))
for s in sk['sockets']: print(s['type'], np.array(s['matrix']).reshape(4, 4)[:3, 3].round(2))
def S(p, n=30000): V, T = F.stl(p); return F.surf(V.astype(float), T, n, 0)
C, M, SH, PR = S(CAP + 'Torso.stl'), S(MF), S(CAP + 'Tilt Shield.stl'), S(CAP + 'Pauldron r.stl')
print('captain torso centroid', C.mean(0).round(2), 'shield', SH.mean(0).round(2), 'pad r', PR.mean(0).round(2))
print('mar fil torso centroid', M.mean(0).round(2))
best = None
for R0 in rots24():
    for s0 in (0.9,):
        t0 = M.mean(0) - s0 * R0 @ C.mean(0)
        r = sicp(C, M, R0, t0, s0, it=25, scale=False)
        if best is None or r[3] < best[3]: best = r
R, t, s, med, p95 = sicp(C, M, best[0], best[1], best[2], it=100, scale=False)
print('rigid@0.9: R', R.round(3).tolist(), 't', t.round(2), 'median %.3f p95 %.3f' % (med, p95))
R2, t2, s2, med2, p952 = sicp(C, M, R, t, s, it=100, scale=True)
print('similarity: scale %.3f median %.3f p95 %.3f, rot diff %.1f deg' % (s2, med2, p952, np.degrees(np.arccos(np.clip((np.trace(R.T @ R2) - 1) / 2, -1, 1)))))
np.savez('cap2mf.npz', R=R, t=t, s=s, R2=R2, t2=t2, s2=s2)
for nm, P in (('shield', SH), ('pad r', PR)):
    print(nm, 'in Mar Fil frame (0.9):', (s * P.mean(0) @ R.T + t).round(2), ' (similarity):', (s2 * P.mean(0) @ R2.T + t2).round(2))
