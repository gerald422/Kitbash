"""Old Style Space Knight MK8 torsos (no `exact`: the types have no rock or settle, so they land as fitted), chest equipment and neck guards -> Kitbash Library files + sidecars.

Sources (Josh's PC):
  D:\\new cults\\Old_style_space_knight_torso\\<A-I>\\<X[.00k]>.stl   72 torsos on a print grid, each with a back collar
  D:\\new cults\\Old_style_space_knight_alien_hunter_turtlenecks\\MK8 torso BUILDER.blend
      the same 72 torsos without the collar (so the turtleneck guards fit), Chest_equipment_1-5_L/R, Neck_1-8,
      all in Mar Fil's kit frame turned 90 deg (front +X) and moved to y = -156.854.
Library (Josh, Nov 3): the collarless builder torsos; the collar is a ninth neck option; maker "Old Style Space Knight".
Everything is written in the Mar Fil kit frame (Z up, front +Y, x = 0 on the centre line):
  kit = (-(y - YC), x, z) of the builder's world coordinates, YC = -156.854 (the torsos' mirror plane).
python build.py MESHES_NPZ STL_A OUT"""
import json, os, sys, struct
import numpy as np
from scipy.spatial import cKDTree

NPZ, STL_A, OUT = sys.argv[1:4]
YC = -156.854
MAKER_DIR = "Old Style Space Knight - Heresy"; KIT = "MK8"; PRE = "OldStyle MK8 - "
SRC_T = "Old_style_space_knight_torso"; SRC_B = "Old_style_space_knight_alien_hunter_turtlenecks\\MK8 torso BUILDER.blend"
LIB = os.path.join(os.path.dirname(__file__), "..", "..", "library")
TORSO1 = os.path.join(LIB, "Mar Fil - Tacticus", "AssaultMarines-V2", "Chests", "MarFil Assault - Torso 1.sockets.json")
A = np.diag([-1.0, 1, 1, 1])
Z = np.load(NPZ)


def kit(v):
    v = np.asarray(v, float); return np.c_[-(v[:, 1] - YC), v[:, 0], v[:, 2]]


def write_stl(path, V, T):
    tri = V[T].astype(np.float32); n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True); n = (n / np.where(ln == 0, 1, ln)).astype(np.float32)
    rec = np.zeros(len(T), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])); rec["n"] = n; rec["v"] = tri
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"Kitbash: Old Style Space Knight MK8 (Mar Fil kit frame)".ljust(80, b" ")); f.write(struct.pack("<I", len(T))); f.write(rec.tobytes())


def mesh(name):
    V = kit(Z[name + "|v"]); T = Z[name + "|t"]
    used = np.unique(T); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))   # drop loose vertices
    return V[used], remap[T]


def flat(M): return [round(float(x), 6) for x in np.asarray(M).reshape(-1)]


def sock(part, typ, M, how, size=2.0):
    return {"type": typ, "name": f"{part}_socket_{typ}", "matrix": flat(M), "display_type": "ARROWS", "display_size": size,
            "props": {"tiow_from": how}}


def frame(o, z, up=(0, 0, 1)):
    z = np.asarray(z, float); z /= np.linalg.norm(z); y = np.asarray(up, float) - z * np.dot(up, z); y /= np.linalg.norm(y)
    M = np.eye(4); M[:3, 0] = np.cross(y, z); M[:3, 1] = y; M[:3, 2] = z; M[:3, 3] = o; return M


def surface(V, T, n=200000, seed=3):
    r = np.random.default_rng(seed); a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; cr = np.cross(b - a, c - a); ar = np.linalg.norm(cr, axis=1)
    k = ar > 0; a, b, c, cr, ar = a[k], b[k], c[k], cr[k], ar[k]
    i = r.choice(len(a), n, p=ar / ar.sum()); u, w = r.random(n), r.random(n); m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]
    return a[i] + u[:, None] * (b[i] - a[i]) + w[:, None] * (c[i] - a[i]), cr[i] / ar[i, None]


out_rows = []    # (library path, source, category, fit)
def emit(folder, name, V, T, side):
    rel = os.path.join(MAKER_DIR, KIT, folder, name + ".stl"); write_stl(os.path.join(OUT, rel), V, T)
    json.dump(side, open(os.path.join(OUT, rel[:-4] + ".sockets.json"), "w"), indent=1)
    out_rows.append((rel.replace("/", "\\"), side["original"]["path"], side["category"], ",".join(side.get("fits", {}))))


# --- sockets shared by every torso -----------------------------------------------------------------------------------
t1 = {s["type"]: np.array(s["matrix"]).reshape(4, 4) for s in json.load(open(TORSO1))["sockets"]}
TA, TT = mesh("A"); S, N = surface(TA, TT)
# Chest Equip L: under the left chest piece's footprint, Z out of the chest, Y up (same piece on every torso: the
# torsos share one body; the designs only add detail)
eq = [mesh(f"Chest_equipment_{k}_L")[0] for k in range(1, 6)]
foot = np.vstack([e[cKDTree(S).query(e)[0] < 0.25] for e in eq])
d, j = cKDTree(S).query(foot.mean(0)); o = S[j]; nrm = N[cKDTree(S).query(foot)[1]].mean(0)
SL = frame(o, nrm); SR = A @ SL @ A
NG = np.eye(4); NG[:3, 3] = (0.0, t1["Neck"][1, 3], t1["Neck"][2, 3])     # the head seat, axes of the kit frame
print("Chest Equip L at", o.round(3), "normal", (nrm / np.linalg.norm(nrm)).round(3), "| Neck Guard at", NG[:3, 3].round(3))

HOW_T1 = "Mar Fil Assault Torso 1's socket: the builder torsos are made in Mar Fil's kit frame (Nov 3 check: waist dome, head seat 0.03 mm, back 0.08 mm, shoulder faces 0.05 mm)"
NOTE_T = ("MK8 torso builder: the source STL without its back collar (that collar is 'Neck Guard Collar'), turned into the "
          "Mar Fil kit frame from the builder blend (kit = (-(y+156.854), x, z)); Mar Fil Torso 1's sockets")
for L in "ABCDEFGHI":
    for k in range(10):
        ob = L if k == 0 else f"{L}.{k:03d}"
        if ob + "|v" not in Z: continue
        V, T = mesh(ob); part = f"{PRE}Torso {L}{k}"
        socks = [sock(part, t, t1[t], HOW_T1, 3.0) for t in ("Shoulder R", "Shoulder L", "Neck", "Back", "Waist")]
        socks += [sock(part, "Chest Equip L", SL, "under the builder's left chest equipment, Z out of the chest, Y up"),
                  sock(part, "Chest Equip R", SR, "mirror of Chest Equip L"),
                  sock(part, "Neck Guard", NG, "the head seat (Mar Fil Neck socket position), kit axes: the builder's neck guards sit here")]
        emit("Chests", part, V, T, {"schemaVersion": 1, "part": ob, "category": "Chests", "sockets": socks, "fits": {},
                                     "notes": {"source": NOTE_T},
                                     "original": {"name": ob, "folder": L, "path": f"new cults\\{SRC_T}\\{L}\\{ob}.stl"}})

for k in range(1, 6):
    V, T = mesh(f"Chest_equipment_{k}_L"); part = f"{PRE}Chest Equipment {k} L"
    emit("Chest Equipment", part, V, T, {
        "schemaVersion": 1, "part": f"Chest_equipment_{k}_L", "category": "Chest Equipment", "sockets": [],
        "fits": {"Chest Equip L": flat(np.linalg.inv(SL))},
        "notes": {"Chest Equip L": "where the builder blend has it (kit frame = the torso's)", "source": "exported from the builder blend"},
        "original": {"name": f"Chest_equipment_{k}_L", "folder": "Chest_equipment", "path": f"new cults\\{SRC_B}#Chest_equipment_{k}_L"},
        "variants": [{"side": "R", "mirror": True, "align": flat(A), "name": f"{PRE}Chest Equipment {k} R",
                      "title": f"{PRE}Chest Equipment {k} R", "folder": "Chest Equipment",
                      "from": "mirror (the builder's R piece is the mirror of L: median 0.04, max 0.07 mm)", "match": 0.04,
                      "sidecar": {"category": "Chest Equipment", "fits": {"Chest Equip R": flat(np.linalg.inv(SR))}, "sockets": []}}]})

NOTE_N = "where the builder blend has it (kit frame = the torso's); goes with the collarless torsos"
for k in range(1, 9):
    V, T = mesh(f"Neck_{k}"); part = f"{PRE}Neck Guard {k}"
    emit("Neck Guards", part, V, T, {
        "schemaVersion": 1, "part": f"Neck_{k}", "category": "Neck Guards", "sockets": [], "fits": {"Neck Guard": flat(np.linalg.inv(NG))},
        "notes": {"Neck Guard": NOTE_N, "source": "exported from the builder blend"},
        "original": {"name": f"Neck_{k}", "folder": "Neck_protection", "path": f"new cults\\{SRC_B}#Neck_{k}"}})

# the original back collar: its own piece in every source torso STL (registered: source A + (0, -157.177, 0) = builder A)
b = open(STL_A, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
v = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))["v"].reshape(-1, 3).astype(float)
V, inv = np.unique(v, axis=0, return_inverse=True); T = inv.reshape(-1, 3); V = V + [0, -157.177, 0]
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
r_, c_ = np.r_[T[:, 0], T[:, 1]], np.r_[T[:, 1], T[:, 2]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(len(V), len(V))), directed=False)
tb = cKDTree(Z["A|v"].astype(float)); far = tb.query(V)[0] > 0.05
coll = np.unique(lab[far]); assert len(coll) == 1, coll
keep = lab == coll[0]; idx = -np.ones(len(V), int); idx[keep] = np.arange(keep.sum()); Tc = idx[T[keep[T[:, 0]]]]
part = f"{PRE}Neck Guard Collar"
emit("Neck Guards", part, kit(V[keep]), Tc, {
    "schemaVersion": 1, "part": "collar", "category": "Neck Guards", "sockets": [], "fits": {"Neck Guard": flat(np.linalg.inv(NG))},
    "notes": {"Neck Guard": "the source torsos' own back collar, where it is on them", "source": f"the back collar piece of {SRC_T}\\A\\A.stl (same on every torso)"},
    "original": {"name": "A", "folder": "A", "path": f"new cults\\{SRC_T}\\A\\A.stl"}})
json.dump(out_rows, open(os.path.join(OUT, "_rows.json"), "w"), indent=0)
print(len(out_rows), "parts written")
