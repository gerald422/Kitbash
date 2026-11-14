"""kb.connect finds a connector on a part from scratch (notes 098). Made-up shapes, nothing from the library:
a lumpy closed body, a patch of it cut out as the connector, the body moved / turned / mirrored; find() must put the
patch back where it came from. Runs in Blender (numpy + Blender's KD tree), about 15 s; "Run checks.bat" runs it.

    blender --background --factory-startup --python tests/kb/t_connect.py
Exit code 1 on a failure."""
import os, sys
import numpy as np
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, R)
from kb import connect as C, geo

fails = []


def ok(cond, what):
    if not cond: fails.append(what)


def body(n=90):
    """a lumpy closed body about 20 x 14 x 12 mm, faces outward, as triangles (no symmetry to fool the search)"""
    u = np.linspace(0, np.pi, n); v = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False)
    U, V = np.meshgrid(u, v, indexing="ij")
    r = 1 + 0.18 * np.sin(3 * U) * np.cos(2 * V + 0.4) + 0.12 * np.cos(5 * V) * np.sin(U) ** 2 + 0.08 * np.sin(7 * U + V)
    P = np.stack([10 * r * np.sin(U) * np.cos(V), 7 * r * np.sin(U) * np.sin(V), 6 * r * np.cos(U)], -1)
    tri = []
    for i in range(n - 1):
        for j in range(2 * n):
            a, b, c, d = P[i, j], P[i, (j + 1) % (2 * n)], P[i + 1, j], P[i + 1, (j + 1) % (2 * n)]
            tri += [(a, c, b), (b, c, d)]
    T = np.array(tri); fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); T = T[np.linalg.norm(fn, axis=1) > 1e-12]
    out = np.einsum("ij,ij->i", np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), T.mean(1)) < 0
    T[out] = T[out][:, [0, 2, 1]]                                                        # faces outward
    return T


def patch(T, at, r):
    return T[np.linalg.norm(T.mean(1) - at, axis=1) < r]


def moved(T, Rm, t): return T @ Rm.T + t


T = body(); con = C.Connector(patch(T, T[len(T) // 3].mean(0), 2.6), "made-up")
rng = np.random.default_rng(3)
for case in range(3):
    ax = rng.normal(size=3); Rm = C._rot(ax, 40 + 50 * case); t = rng.normal(size=3) * 5
    f = C.find(con, C.Surface(moved(T, Rm, t)), file_turn=False)
    want = Rm @ con.c + t; got = f["M"][:3, :3] @ con.c + f["M"][:3, 3]
    ok(f["same"], "case %d: found it (match %.4f, cover %.2f)" % (case, f["match"], f["cover"]))
    ok(np.linalg.norm(got - want) < 0.1, "case %d: in place (%.3f mm off)" % (case, np.linalg.norm(got - want)))
    ok(geo.ang(f["M"][:3, :3] @ Rm.T) < 2.0, "case %d: turned right (%.2f deg off)" % (case, geo.ang(f["M"][:3, :3] @ Rm.T)))
# a left part: the library mirrors it back to a right one; Surface(mirror=True) must give the original, faces outward
mir = (T * np.array([-1.0, 1, 1]))[:, [0, 2, 1]]
f = C.find(con, C.Surface(mir, mirror=True), file_turn=False)
ok(f["same"] and np.linalg.norm(f["M"][:3, 3]) < 0.1 and geo.ang(f["M"][:3, :3]) < 2.0, "mirrored part: found in place (%s)" % f["match"])
# another design: a patch with 0.3 mm ripples the body doesn't have must not be taken for this one
Q = patch(T, T[2 * len(T) // 3].mean(0), 2.6); nq = Q.mean((0, 1)) / np.linalg.norm(Q.mean((0, 1)))
other = C.Connector(Q + 0.3 * np.sin(2 * np.pi * Q[..., :1] / 1.2) * nq, "rippled")
f = C.find(other, C.Surface(T), file_turn=False)
ok(not f["same"], "a different shape is not 'same' (match %.4f, cover %.2f)" % (f["match"], f["cover"]))

print("t_connect: %d failed" % len(fails) + "".join("\n  FAIL " + x for x in fails))
sys.exit(1 if fails else 0)
