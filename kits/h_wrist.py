import geo, json, numpy as np
from scipy.spatial import cKDTree
C = json.load(open('/home/claude/sock/carry.json'))
def raw_socks(name):
    c = C[name]; Ti = np.linalg.inv(np.array(c['T']))
    return {s['type']: Ti @ np.array(s['matrix']).reshape(4, 4) for s in c['sidecar']['sockets']}, c['src']
def plane_near(V, T, p, n, r=2.5):
    """triangles within r of p whose normal is within 25 deg of n: area-weighted centre/normal/spread."""
    A, B, Cc = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    cen = (A + B + Cc) / 3; nn = np.cross(B - A, Cc - A); ar = np.linalg.norm(nn, axis=1); nn = nn / np.maximum(ar[:, None], 1e-12)
    k = (np.linalg.norm(cen - p, axis=1) < r) & (np.abs(nn @ n) > 0.9)
    if not k.any(): return None
    w = ar[k]; c = (cen[k] * w[:, None]).sum(0) / w.sum(); m = (nn[k] * np.sign(nn[k] @ n)[:, None] * w[:, None]).sum(0); m /= np.linalg.norm(m)
    d = (cen[k] - c) @ m
    return c, m, w.sum() / 2, np.abs(d).max()
for name in ['101-Arm-6-R-A', '102-Arm-6-R-B', '76-Arm-1-R-A', '126-Arm-11-R-A', '37-Arm-1-B']:
    S, src = raw_socks(name); V, T = geo.load(src)
    for k, M in S.items():
        p, z = M[:3, 3], M[:3, 2]
        r = plane_near(V, T, p, z)
        if r is None: print(name, k, 'no plane'); continue
        c, m, area, flat = r
        print('%-15s %-15s sock %s z %s | plane c %s n %s area %.1f flat %.3f  off-plane %.3f in-plane %.3f' % (
            name, k, np.round(p, 2), np.round(z, 2), np.round(c, 2), np.round(m, 2), area, flat, (p - c) @ m, np.linalg.norm((p - c) - ((p - c) @ m) * m)))
