import sys, json, numpy as np
exec(open("/home/claude/test/v16/variants_find.py").read().split("L = \"/home")[0])
T._spheres = spheres_var("C")
src = T.find_shin_points
L = "/home/claude/test/padlib/Mar Fil - Tacticus/Kit/Legs/"
items = []
for pre, knee in (("tech_parts", "Knee-L-Pose"), ("chap_parts", "Knee-A-Pose.L")):
    V, Tr, _ = rig("/home/claude/blend/mf/" + pre, knee); items.append((pre,) + merge(V, Tr))
for legs in ("29-Legs-2", "35-Legs-2-A"):
    items.append((legs,) + tuple(T.read_stl_np(L + legs + ".stl")))
for nm, V, Tr in items:
    N = T._vertex_normals(V, Tr)
    holes = []
    for r in (1.92, 1.97, 2.02):
        for c, rr, on in T._spheres(V, N, r, -1, minvotes=60):
            if all(np.linalg.norm(c - h[0]) > 1.0 for h in holes): holes.append((c, rr, on))
    for ea, eb, top, op in T.find_shin_points(V, Tr):
        u = (eb - ea) / np.linalg.norm(eb - ea)
        h = min(holes, key=lambda h: np.linalg.norm(h[0] - top))
        c, r = h[0], h[1]
        mid = 0.5 * (ea + eb); up = c - mid; up -= u * (up @ u); up /= np.linalg.norm(up)
        d = np.linalg.norm(V - c, axis=1); cup = V[np.abs(d - r) < 0.06]
        hs = (cup - c) @ up; best = np.sort(hs)[-6:]
        along = (cup - c) @ u
        top6 = cup[np.argsort(-hs)[:6]]
        print("%-12s r %.3f top along %.3f, up %.3f; next-highest up %s along %s" % (nm, r, (top - c) @ u, (top - c) @ up, np.round(best[::-1], 3), np.round((top6 - c) @ u, 2)))
