"""Pauldrons that sink in: the pad-62 match puts a pad's outer shell where 62's is, but the WarGame Exclusive pads
are thicker inside, so the inside of the dome cuts into the top of the shoulder. Push each one out (the mean way out
of the points inside: towards their nearest arm/torso surface, reversed) in 0.05 mm steps until it cuts in no deeper
than 0.4 mm, at most 1 mm (Josh's 62 on Mar Fil Assault Arm 1A R, on Torso 1, as the reference).
Run with the bpy venv: python padlift.py -- PADS.json TESTLIB OUT.json [NEW_CULTS/ LIBRARY/]"""
import json, os, sys, numpy as np
import bpy  # noqa: F401  (mathutils comes with it)
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; PADS, TL, OUTF = a[:3]
U = a[3] if len(a) > 3 else "/mnt/user-data/uploads/d/new cults/"
LIBU = a[4] if len(a) > 4 else "/mnt/user-data/uploads/d/Kitbash Library/"
def stl(p):
    d = np.fromfile(p, dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), offset=84)
    return d['v'].reshape(-1, 3).astype(float)
def M(m): return np.array(m, float).reshape(4, 4)
def tf(W, V): return (np.c_[V, np.ones(len(V))] @ W.T)[:, :3]
def bvh(V): return BVHTree.FromPolygons([Vector(v) for v in V], [(3*i, 3*i+1, 3*i+2) for i in range(len(V) // 3)])
D3 = [Vector(d).normalized() for d in ((0.0123, 0.0177, 1), (1, 0.031, -0.017), (-0.023, -1, 0.041))]
def odd(t, v, d):
    k = 0; q = v.copy()
    for _ in range(12):
        h = t.ray_cast(q, d, 500)
        if h[0] is None: break
        k += 1; q = h[0] + d * 1e-4
    return k % 2
def cut(trees, P):
    deep = 0.0
    for v in P:
        v = Vector(v)
        for t in trees:
            d = t.find_nearest(v)[3]
            if d > deep and d < 4 and all(odd(t, v, dd) for dd in D3): deep = d
    return deep
tor = json.load(open(TL + "/MarFil/MarFil Assault - Torso 1.sockets.json")); arm = json.load(open(TL + "/MarFil/MarFil Assault - Arm 1A R.sockets.json"))
S_sh = M(next(s for s in tor["sockets"] if s["type"] == "Shoulder R")["matrix"]); W_arm = S_sh @ M(arm["fits"]["Shoulder R"])
S_pad = W_arm @ M(next(s for s in arm["sockets"] if s["type"] == "Pad R")["matrix"])
trees = [bvh(stl(TL + "/MarFil/MarFil Assault - Torso 1.stl")), bvh(tf(W_arm, stl(TL + "/MarFil/MarFil Assault - Arm 1A R.stl")))]
P62 = "Mar Fil - Tacticus/AssaultMarines-V2/Shoulder Pads/MarFil Assault - Shoulder Pad 1"
F62 = M(json.load(open(LIBU + P62 + ".sockets.json"))["fits"]["Pad R"]); V62 = stl(LIBU + P62 + ".stl")
base = cut(trees, tf(S_pad @ F62, V62[::max(1, len(V62) // 4000)]))
print("62 on Arm 1A R cuts %.2f mm" % base, flush=True)
pads = json.load(open(PADS)); out = json.load(open(OUTF)) if os.path.exists(OUTF) else {}
def push_dir(trees, P):
    acc = np.zeros(3); n = 0
    for v in P:
        vv = Vector(v)
        for t in trees:
            loc, nrm, _i, d = t.find_nearest(vv)
            if d > 0.2 and d < 4 and all(odd(t, vv, dd) for dd in D3): acc += np.array(loc - vv); n += 1
    return acc / np.linalg.norm(acc) if n else None
for rel, r in pads.items():
    if rel in out: continue
    V = stl(U + rel) * r.get("scale", 1.0); V = V[::max(1, len(V) // 4000)]; F = M(r["fit"]); W0 = S_pad @ F   # fits are in the maker's scaled coords
    c0 = c = cut(trees, tf(W0, V)); move = np.zeros(3); d = push_dir(trees, tf(W0, V)) if c0 > 0.45 else None
    while d is not None and c > 0.4 and np.linalg.norm(move) < 1.0:
        move = move + 0.05 * d; L = np.eye(4); L[:3, 3] = move; c = cut(trees, tf(L @ W0, V))
    # the move in the pad socket's frame, so it goes into the fit: fit' = inv(S_pad) @ T(move) @ S_pad @ fit
    L = np.eye(4); L[:3, 3] = move; Fn = np.linalg.inv(S_pad) @ L @ S_pad @ F
    out[rel] = {"cut_before": round(c0, 3), "moved_mm": round(float(np.linalg.norm(move)), 2), "dir_in_socket": (np.linalg.inv(S_pad)[:3, :3] @ move).round(3).tolist(),
                "cut_after": round(c, 3), "fit": [round(float(x), 6) for x in Fn.ravel()]}
    print("%-48s cut %.2f -> moved %.2f mm -> %.2f" % (rel[-48:], c0, np.linalg.norm(move), c), flush=True)
    json.dump(out, open(OUTF, "w"), indent=1)
