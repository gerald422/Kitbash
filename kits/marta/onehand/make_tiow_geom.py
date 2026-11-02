"""Write tiow_geom.py: TIOW Inbox's top-level functions and constants without Blender (classes and bpy calls dropped),
so its wrist and hand rules run on the PC's plain Python. Usage: python make_tiow_geom.py tiow_inbox.py tiow_geom.py"""
import ast, sys
src = open(sys.argv[1], encoding='utf-8').read(); tree = ast.parse(src)
out = ['import types, sys as _sys',
       "for _m in ('bpy', 'bpy.types', 'bpy.props', 'mathutils', 'bpy_extras', 'bmesh'): _sys.modules.setdefault(_m, types.ModuleType(_m))",
       'class _Any:', '    def __getattr__(self, k): return _Any()', '    def __call__(self, *a, **k): return _Any()',
       "import bpy, mathutils; bpy.types = bpy.props = bpy.app = bpy.utils = bpy.ops = bpy.data = bpy.context = _Any(); mathutils.Matrix = mathutils.Vector = _Any()"]
for node in tree.body:
    seg = ast.get_source_segment(src, node)
    if isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom)):
        if isinstance(node, (ast.Import, ast.ImportFrom)): out.append('try:\n' + '\n'.join('    ' + l for l in seg.splitlines()) + '\nexcept Exception: pass')
        else: out.append(seg)
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        out.append('try:\n' + '\n'.join('    ' + l for l in seg.splitlines()) + '\nexcept Exception: pass')
open(sys.argv[2], 'w', encoding='utf-8').write('\n\n'.join(out) + '\n')
# Blender's BVH nearest -> exact closest point on the k triangles with the nearest centroids (scipy)
open(sys.argv[2], 'a', encoding='utf-8').write('''

def _bvh_nearest(V, T):
    """Closest points on a mesh (V, T) to points P: (points, distances). (Blender-free: k nearest triangles, exact.)"""
    import numpy as np
    from scipy.spatial import cKDTree
    V = np.asarray(V, float); T = np.asarray(T)
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    tree = cKDTree((A + B + C) / 3)
    ext = np.maximum(np.linalg.norm(A - B, axis=1), np.maximum(np.linalg.norm(B - C, axis=1), np.linalg.norm(C - A, axis=1)))
    def closest(P, a, b, c):
        ab, ac, ap = b - a, c - a, P - a
        d1, d2 = (ab * ap).sum(-1), (ac * ap).sum(-1)
        bp = P - b; d3, d4 = (ab * bp).sum(-1), (ac * bp).sum(-1)
        cp = P - c; d5, d6 = (ab * cp).sum(-1), (ac * cp).sum(-1)
        va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
        den = np.where(np.abs(va + vb + vc) < 1e-18, 1e-18, va + vb + vc)
        v = vb / den; w = vc / den
        R = a + ab * v[..., None] + ac * w[..., None]
        def seg(p, s, e):
            se = e - s; t = np.clip(((p - s) * se).sum(-1) / np.maximum((se * se).sum(-1), 1e-18), 0, 1); return s + se * t[..., None]
        out = [R, seg(P, a, b), seg(P, b, c), seg(P, c, a)]
        inside = (va >= 0) & (vb >= 0) & (vc >= 0)
        D = np.stack([np.linalg.norm(o - P, axis=-1) for o in out], -1)
        D[..., 0] = np.where(inside, D[..., 0], np.inf)
        k = D.argmin(-1)
        Q = np.choose(k[..., None], [o for o in out]) if False else np.take_along_axis(np.stack(out, -2), k[..., None, None].repeat(3, -1), -2)[..., 0, :]
        return Q, D.min(-1)
    def nearest(P):
        P = np.asarray(P, float); kk = min(64, len(T))
        _, idx = tree.query(P, k=kk)
        Pa = P[:, None, :].repeat(kk, 1)
        Q, d = closest(Pa, A[idx], B[idx], C[idx])
        j = d.argmin(1); r = np.arange(len(P))
        return Q[r, j], d[r, j]
    return nearest
''')
