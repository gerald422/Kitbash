"""Rule: an arm's wrist socket from its shape. Origin = centre of the flat wrist face at the far end of the arm,
Y = into the arm (along the forearm), Z = across the wrist (the major axis of an oval wrist, else a default)."""
import numpy as np
def tri_info(V, T):
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(B - A, C - A); a = np.linalg.norm(n, axis=1)
    return (A + B + C) / 3, n / np.maximum(a[:, None], 1e-12), a / 2
def _components(idx, cen, link):
    """group triangle indices whose centroids are within `link` (grid-based union-find)"""
    P = cen[idx]; key = np.floor(P / link).astype(np.int64)
    parent = list(range(len(idx)))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    cells = {}
    for i, k in enumerate(map(tuple, key)): cells.setdefault(k, []).append(i)
    for k, members in cells.items():
        near = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    near += cells.get((k[0] + dx, k[1] + dy, k[2] + dz), [])
        for i in members:
            for j in near:
                if j > i and np.sum((P[i] - P[j]) ** 2) < link * link:
                    ri, rj = find(i), find(j)
                    if ri != rj: parent[ri] = rj
    groups = {}
    for i in range(len(idx)): groups.setdefault(find(i), []).append(idx[i])
    return [np.array(g) for g in groups.values()]
def boundary(T, sel):
    """edges of the selected triangles used only once (the face outline)"""
    E = np.sort(np.concatenate([T[sel][:, [0, 1]], T[sel][:, [1, 2]], T[sel][:, [2, 0]]]), axis=1)
    u, c = np.unique(E, axis=0, return_counts=True)
    return u[c == 1]
def circle_fit(P2):
    A = np.c_[2 * P2, np.ones(len(P2))]; b = (P2 ** 2).sum(1)
    s, *_ = np.linalg.lstsq(A, b, rcond=None); c = s[:2]; r = np.sqrt(s[2] + c @ c)
    return c, r
def wrist_frame(V, T, joint, default_up, area=(3.0, 25.0), verbose=False):
    V = np.asarray(V, float); cen, n, a = tri_info(V, T)
    dist = np.linalg.norm(cen - joint, axis=1); far = dist > 0.55 * dist.max()
    # flat faces: bin normals and plane offsets
    cand = []
    idx = np.where(far)[0]
    key = np.round(n[idx] * 12).astype(int)
    bins = {}
    for i, k in zip(idx, map(tuple, key)): bins.setdefault(k, []).append(i)
    for k, ii in bins.items():
        ii = np.array(ii)
        if a[ii].sum() < area[0]: continue
        nn = (n[ii] * a[ii, None]).sum(0); nn /= np.linalg.norm(nn)
        ii = ii[(n[ii] @ nn) > 0.995]
        off = cen[ii] @ nn
        for o in np.unique(np.round(off / 0.04)):
            sel = ii[np.abs(off / 0.04 - o) < 0.75]
            if a[sel].sum() < area[0]: continue
            for g in _components(sel, cen, 0.8):
                A = a[g].sum()
                if not (area[0] <= A <= area[1]): continue
                c = (cen[g] * a[g, None]).sum(0) / A
                out = c - joint
                if (out @ nn) < 0.3 * np.linalg.norm(out): continue     # must face away from the shoulder
                cand.append((A, g, nn, c))
    if not cand: return None
    # the outermost good-sized flat face
    cand.sort(key=lambda x: -np.linalg.norm(x[3] - joint))
    A, g, nn, c = cand[0]
    E = boundary(T, g); B = V[np.unique(E)]
    Y = -nn
    X0 = np.cross(Y, [0, 0, 1.0]) if abs(Y[2]) < 0.9 else np.cross(Y, [1.0, 0, 0]); X0 /= np.linalg.norm(X0); Z0 = np.cross(X0, Y)
    P2 = np.c_[(B - c) @ X0, (B - c) @ Z0]
    cc, r = circle_fit(P2)
    origin = c + cc[0] * X0 + cc[1] * Z0
    # the wall just inside the face: an oval wrist gives the roll
    L = V - origin; dep = L @ Y
    ring = V[(dep > 0.15) & (dep < 0.6) & (np.linalg.norm(L - dep[:, None] * Y, axis=1) < 1.5 * r)]
    if len(ring) < 12: ring = B
    Q = np.c_[(ring - origin) @ X0, (ring - origin) @ Z0]; Q = Q - Q.mean(0)
    w, v = np.linalg.eigh(np.cov(Q.T)); aspect = np.sqrt(w[1] / max(w[0], 1e-12))
    u = np.asarray(default_up, float); zr = u - (u @ Y) * Y; zr /= np.linalg.norm(zr)
    if aspect > 1.1:
        m = v[:, 1][0] * X0 + v[:, 1][1] * Z0
        Z = m if m @ zr >= 0 else -m
    else:
        Z = zr
    Z = Z - (Z @ Y) * Y; Z /= np.linalg.norm(Z); X = np.cross(Y, Z)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = X, Y, Z, origin
    if verbose: print('   face area %.1f r %.2f aspect %.2f, %d candidates' % (A, r, aspect, len(cand)))
    return M

def stub_caps(V, T, area=(2.5, 16.0), verbose=False):
    """Flat faces that cap the end of a round stub (a wrist): a closed oval face with the stub's wall
    right behind it all the way round and nothing in front. Returns [(score, centre, normal(out), r, ring pts)]."""
    V = np.asarray(V, float); cen, n, a = tri_info(V, T)
    out = []
    key = np.round(n * 12).astype(int); bins = {}
    for i, k in enumerate(map(tuple, key)): bins.setdefault(k, []).append(i)
    for k, ii in bins.items():
        ii = np.array(ii)
        if a[ii].sum() < area[0]: continue
        nn = (n[ii] * a[ii, None]).sum(0); nn /= np.linalg.norm(nn)
        ii = ii[(n[ii] @ nn) > 0.995]
        off = cen[ii] @ nn
        for o in np.unique(np.round(off / 0.04)):
            sel = ii[np.abs(off / 0.04 - o) < 0.75]
            if a[sel].sum() < area[0]: continue
            for g in _components(sel, cen, 0.8):
                A = a[g].sum()
                if not (area[0] <= A <= area[1]): continue
                B = V[np.unique(boundary(T, g))]
                c0 = (cen[g] * a[g, None]).sum(0) / A
                X0 = np.cross(nn, [0, 0, 1.0]) if abs(nn[2]) < 0.9 else np.cross(nn, [1.0, 0, 0]); X0 /= np.linalg.norm(X0); Z0 = np.cross(X0, nn)
                cc, r = circle_fit(np.c_[(B - c0) @ X0, (B - c0) @ Z0])
                c = c0 + cc[0] * X0 + cc[1] * Z0
                L = V - c; h = L @ nn; rad = np.linalg.norm(L - h[:, None] * nn, axis=1)
                front = np.sum((h > 0.05) & (h < 1.5) & (rad < 0.8 * r))
                wall = (h < -0.15) & (h > -0.8) & (rad > 0.6 * r) & (rad < 1.4 * r)
                if wall.sum() < 12 or front > 0: continue
                W = L[wall]; ang = np.degrees(np.arctan2(W @ Z0, W @ X0))
                cover = len(np.unique(np.floor(ang / 15))) / 24.0
                if cover < 0.85: continue
                out.append((A * cover, c, nn, r, V[wall]))
    return out

def hand_frame(V, T, side, area=(2.5, 16.0)):
    """The hand's wrist frame from its shape: origin = centre of the wrist stump's end face, Y = out of the hand
    (into the arm), Z = along the oval wrist; the fist lies on +X for a right hand, -X for a left."""
    V = np.asarray(V, float)
    caps = stub_caps(V, T, area)
    if not caps: return None
    best = None
    for score, c, nn, r, ring in caps:
        # the hand: material close behind the cap (the fist), more of it than any other stub
        L = V - c; h = L @ nn; near = (h < -0.3) & (h > -5.0) & (np.linalg.norm(L, axis=1) < 5.5)
        mass = near.sum()
        if best is None or mass > best[0]: best = (mass, c, nn, r, ring, near)
    mass, c, nn, r, ring, near = best
    Y = nn
    X0 = np.cross(Y, [0, 0, 1.0]) if abs(Y[2]) < 0.9 else np.cross(Y, [1.0, 0, 0]); X0 /= np.linalg.norm(X0); Z0 = np.cross(X0, Y)
    Q = np.c_[(ring - c) @ X0, (ring - c) @ Z0]; Q = Q - Q.mean(0)
    w, v = np.linalg.eigh(np.cov(Q.T)); m = v[:, 1][0] * X0 + v[:, 1][1] * Z0
    Z = m - (m @ Y) * Y; Z /= np.linalg.norm(Z); X = np.cross(Y, Z)
    bulk = (V[near] - c).mean(0)
    want = 1 if side == 'R' else -1
    if (bulk @ X) * want < 0: Z, X = -Z, -X
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = X, Y, Z, c
    return M

ARMOUR_ANGLE = -86.0   # the forearm's armour (vambrace) sits this far round from the wrist's 'up' (right arm)
def _surface(V, T, n, seed=0):
    tri = V[T]; a = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(seed); i = rng.choice(len(T), n, p=a / a.sum())
    u, w = rng.random(n), rng.random(n); m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]
    t = tri[i]; return t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0])
def wrist_frame2(V, T, joint, side, area=(3.0, 25.0)):
    """Right-arm rule on the (mirrored for a left) mesh: face as wrist_frame, roll from where the forearm armour sits."""
    V = np.asarray(V, float); T = np.asarray(T)
    MXv = np.array([-1.0, 1, 1])
    if side == 'L':
        V = V * MXv; T = T[:, ::-1]; joint = np.asarray(joint) * MXv
    M = wrist_frame(V, T, joint, (0, 0, 1.0), area)
    if M is None: return None
    Y, o = M[:3, 1], M[:3, 3]
    S = _surface(V, T, 200000)
    L = S - o; dep = L @ Y; lat = L - dep[:, None] * Y; rad = np.linalg.norm(lat, axis=1)
    k = (dep > 0.3) & (dep < 2.5) & (rad > 1.9) & (rad < 4.5)
    if k.sum() > 50:
        b = lat[k].mean(0)
        e3 = M[:3, 2]; e1 = np.cross(Y, e3)
        beta = np.degrees(np.arctan2(b @ e1, b @ e3)); z = np.radians(beta - ARMOUR_ANGLE)
        Z = np.sin(z) * e1 + np.cos(z) * e3; X = np.cross(Y, Z)
        M[:3, 0], M[:3, 2] = X, Z
    if side == 'L':
        MX = np.diag([-1.0, 1, 1, 1]); M = MX @ M @ MX
    return M
