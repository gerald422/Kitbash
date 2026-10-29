"""Belt anchors by rule, the same frame a clicked anchor has (Z out of the surface, Y up): on the legs' belt at the
right hip, left hip, front and back. Worked out in torso coordinates (the legs seated on the Waist), so they agree
across every kit's legs. M: legs file -> torso coordinates (S_WAIST @ Waist fit)."""
import numpy as np, geo
BELT_Z = 22.5                                     # torso coords: the belt line (waist joint at 29.3)
AXIS = np.array([0.0, 0.57, BELT_Z])
DIRS = {'Hip R': (1, 0, 0), 'Hip L': (-1, 0, 0), 'Belt Front': (0, 1, 0), 'Belt Back': (0, -1, 0)}
def surf_n(V, T, n, seed=0):
    V = np.asarray(V, float); A = V[T]; cr = np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0]); ar = np.linalg.norm(cr, axis=1); ok = ar > 0
    A, cr, ar = A[ok], cr[ok], ar[ok]
    rng = np.random.default_rng(seed); i = rng.choice(len(A), n, p=ar / ar.sum()); u, v = rng.random(n), rng.random(n); f = u + v > 1; u[f], v[f] = 1 - u[f], 1 - v[f]
    return A[i, 0] + u[:, None] * (A[i, 1] - A[i, 0]) + v[:, None] * (A[i, 2] - A[i, 0]), cr[i] / ar[i, None]
def belt_anchors(rel, M):
    V, T = geo.load(rel); P, N = surf_n(V, T, 400000)
    P = P @ M[:3, :3].T + M[:3, 3]; N = N @ M[:3, :3].T
    out = {}
    for name, d in DIRS.items():
        d = np.array(d, float); L = P - AXIS; t = L @ d; lat = np.linalg.norm(L - t[:, None] * d, axis=1)
        k = (t > 0) & (lat < 0.35)
        if k.sum() < 3: continue
        hit = P[k][np.argmax(t[k])]
        near = (np.linalg.norm(P - hit, axis=1) < 0.6) & (N @ d > 0)
        z = N[near].mean(0) if near.any() else d
        y = np.array([0, 0, 1.0]); z = z - y * (z @ y); z /= np.linalg.norm(z); x = np.cross(y, z)
        K = np.eye(4); K[:3, 0], K[:3, 1], K[:3, 2], K[:3, 3] = x, y, z, hit
        out[name] = np.linalg.inv(M) @ K              # in the legs file
    return out
