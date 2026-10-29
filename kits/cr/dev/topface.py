import numpy as np
def merge_flats(FL, ang_deg=3.0, dz=0.12, reach=8.0):
    """merge near-parallel, near-coplanar flat pieces: [(area, normal, centroid), ...] -> same, merged"""
    FL = sorted(FL, key=lambda f: -f[0]); used = [False] * len(FL); out = []; ca = np.cos(np.radians(ang_deg))
    for i, (A, n, c) in enumerate(FL):
        if used[i]: continue
        used[i] = True; grp = [(A, n, c)]
        for j in range(i + 1, len(FL)):
            if used[j]: continue
            Aj, nj, cj = FL[j]
            if nj @ n > ca and abs((cj - c) @ n) < dz and np.linalg.norm(cj - c) < reach:
                used[j] = True; grp.append((Aj, nj, cj))
        At = sum(g[0] for g in grp); nn = sum(g[0] * g[1] for g in grp); nn = nn / np.linalg.norm(nn)
        cc = sum(g[0] * g[2] for g in grp) / At
        out.append((At, nn, cc))
    return out
def top_face(FL, up=(0, 1, 0), cos=0.7, near_top=4.0, ytop=None):
    up = np.asarray(up, float)
    cand = merge_flats([f for f in FL if f[1] @ up > cos])
    if ytop is None: ytop = max(f[2] @ up for f in cand)
    cand = [f for f in cand if f[2] @ up > ytop - near_top]
    return max(cand, key=lambda f: f[0])
