"""Read Josh's base_jumpack.blend (Oct 31) and work out, in each source file's own coordinates:
the TN Mk6 Universal pack's sockets (fins, mechadendrites, toppers), the Techmarine Arm 2 Joint connector's fit on
each fin socket and its wing socket, and each Bladecrow wing's fit on the wing socket.

Josh's meshes are the source files moved (pack, connector: origin moved; wings: OBJ imported, turned and enlarged x1.30), so each
object's mesh is first registered onto its source file (rigid; ICP from 24 axis turns + PCA): G = object world matrix
@ A, A = source file -> mesh data. Everything is then measured with G, scale taken out (the marine's pack is
enlarged 1.11 / 1.27; Josh: keep the library at 1.0).
Writes extract.json. Run: python extract.py BLEND SRC_DIR PACK_STL OUT_JSON"""
import bpy, json, sys, struct
import numpy as np
from mathutils import Matrix
from scipy.spatial import cKDTree
BLEND, SRC, PACK, OUT = sys.argv[sys.argv.index("--") + 1:][:4]
bpy.ops.preferences.addon_enable(module="part_sockets")
bpy.ops.wm.open_mainfile(filepath=BLEND)
O = bpy.data.objects


def verts(o):
    a = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", a); return a.reshape(-1, 3)


def stl(p):
    b = open(p, "rb").read(); n = struct.unpack_from("<I", b, 80)[0]
    a = np.frombuffer(b, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]), count=n, offset=84)
    return np.unique(a["v"].reshape(-1, 3).astype(float).round(5), axis=0)


def obj(p):
    return np.array([[float(x) for x in l.split()[1:4]] for l in open(p) if l.startswith("v ")])


def rots24():
    out = []
    for perm in ([0, 1, 2], [1, 2, 0], [2, 0, 1], [0, 2, 1], [2, 1, 0], [1, 0, 2]):
        for sg in np.array(np.meshgrid([1, -1], [1, -1], [1, -1])).T.reshape(-1, 3):
            R = np.zeros((3, 3)); R[range(3), perm] = sg
            if np.linalg.det(R) > 0: out.append(R)
    return out


def icp(S, D, R0, t0, it=60):
    """Rigid S -> D (points), from R0, t0. Returns R, t, median and 95% residual."""
    tree = cKDTree(D); R, t = R0, t0
    sub = S[np.random.default_rng(0).choice(len(S), min(len(S), 8000), replace=False)]
    for _ in range(it):
        P = sub @ R.T + t
        d, i = tree.query(P)
        keep = d < max(np.percentile(d, 90), 1e-6)
        A, B = sub[keep], D[i[keep]]
        ca, cb = A.mean(0), B.mean(0)
        U, _s, Vt = np.linalg.svd((A - ca).T @ (B - cb))
        Rn = (U @ np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))]) @ Vt).T
        R, t = Rn, cb - Rn @ ca
    d, _ = tree.query(S @ R.T + t)
    return R, t, float(np.median(d)), float(np.percentile(d, 95))


def sicp(S, D, R, t, s, it=60, scale=True):
    """Similarity (or rigid, scale=False) ICP S -> D. Returns R, t, s, median and 95% residual."""
    tree = cKDTree(D)
    sub = S[np.random.default_rng(0).choice(len(S), min(len(S), 8000), replace=False)]
    for _ in range(it):
        d, i = tree.query(s * sub @ R.T + t)
        k = d <= max(np.percentile(d, 90), 1e-9)
        A, B = sub[k], D[i[k]]; ca, cb = A.mean(0), B.mean(0); A0, B0 = A - ca, B - cb
        U, sv, Vt = np.linalg.svd(A0.T @ B0); Dm = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
        R = (U @ Dm @ Vt).T
        if scale:
            s = (sv * np.diag(Dm)).sum() / (A0 ** 2).sum()
        t = cb - s * R @ ca
    d, _ = tree.query(s * S @ R.T + t)
    return R, t, s, float(np.median(d)), float(np.percentile(d, 95))


def register(S, D, scale=False):
    """Source points S onto mesh points D: the best of 24 axis turns (centroids and sizes matched), refined by
    ICP (similarity when `scale`: Josh's wings are the OBJs enlarged). Returns A (source -> mesh), s, median, p95."""
    best = None
    s0 = np.sqrt(((D - D.mean(0)) ** 2).sum(1).mean() / ((S - S.mean(0)) ** 2).sum(1).mean()) if scale else 1.0
    for R0 in rots24():
        t0 = D.mean(0) - s0 * R0 @ S.mean(0)
        r = sicp(S, D, R0, t0, s0, it=15, scale=scale)
        if best is None or r[3] < best[3]:
            best = r
    R, t, s, med, p95 = sicp(S, D, best[0], best[1], best[2], it=100, scale=scale)
    A = np.eye(4); A[:3, :3] = s * R; A[:3, 3] = t
    return Matrix(A.tolist()), s, med, p95


def rigid(M):
    """Scale (and any shear) out: orthonormal rotation keeping Z, then Y; translation kept."""
    M = np.array(M)
    z = M[:3, 2] / np.linalg.norm(M[:3, 2]); y = M[:3, 1] - z * (M[:3, 1] @ z); y /= np.linalg.norm(y)
    x = np.cross(y, z)
    if np.linalg.det(M[:3, :3]) < 0:
        x = -x
    R = np.eye(4); R[:3, 0], R[:3, 1], R[:3, 2], R[:3, 3] = x, y, z, M[:3, 3]
    return Matrix(R.tolist())


def flat(M):
    return [round(float(v), 6) for v in np.array(M).reshape(-1)]


res = {"registration": {}}
G = {}
srcs = {"Mk6_Jumppack_Universal.001": stl(PACK), "Mk6_Jumppack_Universal": stl(PACK)}
cs = stl(SRC + "/connector.stl")
for n in ("Backpack Connector - Arm 2 Joint.004", "Backpack Connector - Arm 2 Joint.005",
          "Backpack Connector - Arm 2 Joint", "Backpack Connector - Arm 2 Joint.001"):
    srcs[n] = cs
WINGS = ["Wing01_OpenR", "Wing02_ClosedR", "Wing03_UpwardsR", "Wing04_WrappedR", "Wing05_DownwardsR", "Wing06_ExtendedR"]
for w in WINGS:
    S = obj(SRC + "/%s.obj" % w)
    for o in O:
        if o.type == 'MESH' and o.name.startswith(w):
            srcs[o.name] = S
SC = {}
for n, S in srcs.items():
    o = O[n]
    key = (id(S), o.data.name)
    A, sc, med, p95 = register(S, verts(o), scale=n.startswith("Wing"))
    G[n] = o.matrix_world @ A
    SC[n] = sc
    res["registration"][n] = {"scale": sc, "median": med, "p95": p95, "det": float(np.linalg.det(np.array(G[n])[:3, :3]))}
    print("registered %-40s scale %.4f median %.4f p95 %.4f det %+.3f" % (n, sc, med, p95, res["registration"][n]["det"]))

# the pack's sockets, in the pack STL's coordinates (scale taken out)
P = G["Mk6_Jumppack_Universal.001"]
NAMES = {"BackPack_fin_l": "Pack Fin L", "BackPack_fin_r": "Pack Fin R", "Mechadendrite_l": "Mechadendrite L",
         "Mechadendrite_r": "Mechadendrite R", "Center_backpack_topper": "Back Top", "backpack_topper_l": "Back Top L"}
pack = O["Mk6_Jumppack_Universal.001"]
res["pack_sockets"] = {}
for c in pack.children:
    t = c.get("ws_type")
    if t in NAMES:
        L = P.inverted() @ c.matrix_world
        res["pack_sockets"][NAMES[t]] = {"matrix": flat(rigid(L)), "from": c.name}
# the same from the unscaled copy (y = 50), to compare
P0 = G["Mk6_Jumppack_Universal"]
res["pack_sockets_unscaled_copy"] = {NAMES[c["ws_type"]]: flat(rigid(P0.inverted() @ c.matrix_world))
                                     for c in O["Mk6_Jumppack_Universal"].children if c.get("ws_type") in NAMES}


def gap_of(sock):
    return 0.0       # Part Sockets types here carry no snap gap (checked: scene ws_types have none set)


# connectors on the marine's pack: L = .004 (as the file), R = .005 (mirrored)
res["connector"] = {}
for n, side in (("Backpack Connector - Arm 2 Joint.004", "L"), ("Backpack Connector - Arm 2 Joint.005", "R")):
    o = O[n]; s = o.parent
    fit = rigid(s.matrix_world.inverted() @ G[n])            # file -> fin socket frame
    ws = [c for c in o.children if c.get("ws_type") in ("wing_l", "wing_r")]
    wsock = rigid(G[n].inverted() @ ws[0].matrix_world) if ws else None   # wing socket in connector file coords
    wing = [g for g in ws[0].children if g.type == 'MESH'][0] if ws else None
    res["connector"][side] = {"on": s["ws_type"], "fit": flat(fit), "det": float(np.linalg.det(np.array(G[n])[:3, :3])),
                              "wing_socket": flat(wsock) if wsock else None, "wing_socket_from": ws[0].name if ws else None,
                              "wing": wing.name if wing else None,
                              "wing_fit": flat(rigid(ws[0].matrix_world.inverted() @ G[wing.name] @ Matrix.Scale(1.0 / SC[wing.name], 4))) if wing else None}
# every wing on every wing socket in the file: its fit (they should agree: the wings share one root)
res["wing_fits"] = []
for o in O:
    if o.name in G and o.name.startswith("Wing") and o.parent is not None and o.parent.get("ws_type") in ("wing_l", "wing_r"):
        F = rigid(o.parent.matrix_world.inverted() @ G[o.name] @ Matrix.Scale(1.0 / SC[o.name], 4))
        res["wing_fits"].append({"wing": o.name, "socket": o.parent["ws_type"], "fit": flat(F), "scale": SC[o.name],
                                 "det": float(np.linalg.det(np.array(G[o.name])[:3, :3]))})
json.dump(res, open(OUT, "w"), indent=1)
print("done")
