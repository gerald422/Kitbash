"""numpy-only helpers shared by the fit builders: the add-on's own shin finder (pulled from
tiow_inbox.py so it is exactly what runs in Blender), the anchor frame rules, ICP."""
import ast, sys, json, numpy as np
sys.path.insert(0, "/home/claude/blend/forclaude"); from stl_io import read_stl
from scipy.spatial import cKDTree
SRC = open("/home/claude/tiow_blender/tiow_inbox.py").read()
_ns = {"np": np}
for node in ast.parse(SRC).body:
    if isinstance(node, ast.FunctionDef) and node.name in ("_vertex_normals", "_spheres", "find_shin_points"):
        exec(compile(ast.Module([node], []), "tiow_inbox", "exec"), _ns)
find_shin_points = _ns["find_shin_points"]
MX3 = np.diag([-1.0, 1, 1]); MX = np.diag([-1.0, 1, 1, 1])
def stl(path):
    v, n, t = read_stl(path); V = np.asarray(v, float); T = np.asarray(t, np.int64)
    q = np.round(V, 5); u, inv = np.unique(q, axis=0, return_inverse=True)
    return u, inv.reshape(-1)[T]
def M4(x, y, z, o):
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = x, y, z, o; return M
def shin_frame(a, b, c, n):
    """tiow_inbox._three_point_frame('Shin', ...)"""
    a, b, c, n = map(np.asarray, (a, b, c, n)); line = (b - a) / np.linalg.norm(b - a); mid = (a + b) / 2
    off = (c - mid) - line * ((c - mid) @ line); x, y = line, off / np.linalg.norm(off); z = np.cross(x, y)
    if z @ n < 0: x, z = -x, -z
    return M4(x, y, z, c)
def pad_frame(a, b, c, forward=None):
    """tiow_inbox._three_point_frame('Pad', ...): Y along the corners (forward if given), Z to the top point."""
    a, b, c = map(np.asarray, (a, b, c)); line = (b - a) / np.linalg.norm(b - a); mid = (a + b) / 2
    off = (c - mid) - line * ((c - mid) @ line); y = line
    if forward is not None and y @ forward < 0: y = -y
    z = off / np.linalg.norm(off); x = np.cross(y, z)
    return M4(x, y, z, c)
def ang(R): return float(np.degrees(np.arccos(np.clip((np.trace(np.asarray(R)[:3, :3]) - 1) / 2, -1, 1))))
def surf(V, T, n, seed=0):
    tri = V[T]; a = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(seed); i = rng.choice(len(T), n, p=a / a.sum()); u, w = rng.random(n), rng.random(n)
    m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]; t = tri[i]
    return t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0])
def kabsch(P, Q):
    cp, cq = P.mean(0), Q.mean(0); U, S, Vt = np.linalg.svd((P - cp).T @ (Q - cq))
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]); R = Vt.T @ D @ U.T; return R, cq - R @ cp
def icp(src, tree, R, t, iters=40, keep=0.85):
    for _ in range(iters):
        P = src @ R.T + t; d, i = tree.query(P); m = d <= np.quantile(d, keep)
        R, t = kabsch(src[m], tree.data[i[m]])
    d, _ = tree.query(src @ R.T + t); return R, t, d
def rots24():
    out = []
    for perm in ((0, 1, 2), (1, 2, 0), (2, 0, 1), (1, 0, 2), (0, 2, 1), (2, 1, 0)):
        for s in ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1), (-1, 1, 1), (1, -1, 1), (1, 1, -1), (-1, -1, -1)):
            R = np.zeros((3, 3)); R[range(3), perm] = s
            if np.linalg.det(R) > 0: out.append(R)
    return out
def best_fit(src, tgt_pts, inits=None, iters=30):
    tree = cKDTree(tgt_pts); best = None
    for R0 in (inits or rots24()):
        t0 = tgt_pts.mean(0) - R0 @ src.mean(0)
        R, t, d = icp(src, tree, R0, t0, iters)
        if best is None or np.median(d) < best[0]: best = (np.median(d), R, t)
    R, t, d = icp(src, tree, best[1], best[2], 80)
    return R, t, d
def pose(R, t):
    M = np.eye(4); M[:3, :3], M[:3, 3] = R, t; return M
