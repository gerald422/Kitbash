"""Chest inserts on Josh's insert torso (Nov 9, Desktop\\for inserts.blend).

Josh's blend holds a Mar Fil Assault Torso 2 with its upper chest cut for an insert
('23-Torso-2.001_AppliedMods_AppliedMods': the mesh in Torso 2's own file coordinates, 98.7%
of its vertices exactly on Torso 2's, the cut x +-5, y 0.8-7.3, z 33-36.4) and one insert
placed on it ('2.001' = HH GEN3 Chest Reinforcement Plate\\2.stl moved by a pure shift, with
object scale 0.99304 x 1.03859 x 1.03859 along its own axes).

Out (staging folder mirroring the library):
- Chests\\MarFil Assault - Torso 2 Insert.stl (the blend's mesh, triangulated, file coords) +
  sidecar: Torso 2's sockets unchanged + 'Chest Insert' (origin = the placed insert's back
  centre, Z out of the chest along the insert's face, Y up along it).
- every insert as a library STL with Josh's scale baked in (TIOW and the page take only a
  uniform 'scale'; a fit with scale in it would be stripped by Save Correction), fit
  'Chest Insert' = inv(S) @ G' @ T(D t_i): G' maps the scaled reference file onto the torso
  (rigid), t_i the shift that puts insert i's back on the reference's (register.py).

Run with the bpy venv: python build.py <stage dir>
"""
import json, os, sys, numpy as np
import bpy, bmesh

BLEND = "/mnt/user-data/uploads/Desktop/for inserts.blend"
U = "/mnt/user-data/uploads/d/new cults/Inserts/"
LIBU = "/mnt/user-data/uploads/d/Kitbash Library/"
T2 = "Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 2"
TORSO = "Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 2 Insert"
REF = "HH GEN3 Chest Reinforcement Plate/2.stl"
REG = "/home/claude/work/inserts/registrations.json"
OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/home/claude/work/inserts/lib"
# the sets: folder -> (short name for the part names)
SETS = {"Anvils of Barbarus Mk3 Torso Insert (1)": "Anvils of Barbarus",
        "HH GEN3 Chest Reinforcement Plate": "HH GEN3",
        "Iron Gorgon Mk3 Torso Insert": "Iron Gorgon",
        "The Crimson-Sand Decapitators GEN3 Torso Insert": "Crimson-Sand",
        "The Crimson-Sand Decapitators GEN3 Torso Insert/clear": "Crimson-Sand Clear"}
INS_DIR = "Bits/Torso Inserts/Chest Inserts/"


def stl_read(p):
    d = np.fromfile(p, dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), offset=84)
    return d['v'].astype(float)


def stl_write(p, T):
    T = np.asarray(T, float); n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    l = np.linalg.norm(n, axis=1); n[l > 0] /= l[l > 0, None]
    rec = np.zeros(len(T), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    rec['n'] = n; rec['v'] = T
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(b'Kitbash Library'.ljust(80, b' ')); f.write(np.uint32(len(T)).tobytes()); f.write(rec.tobytes())


def flat(M):
    return [round(float(x), 6) for x in np.asarray(M).ravel()]


def Tr(v):
    M = np.eye(4); M[:3, 3] = v; return M


bpy.ops.wm.open_mainfile(filepath=BLEND)
to = bpy.data.objects['23-Torso-2.001_AppliedMods_AppliedMods']; io = bpy.data.objects['2.001']
Mt = np.array(to.matrix_world); Mi = np.array(io.matrix_world)

# the torso: triangulated, in its own (= Torso 2's file) coordinates
bm = bmesh.new(); bm.from_mesh(to.data); bmesh.ops.triangulate(bm, faces=bm.faces[:])
TT = np.array([[v.co[:] for v in f.verts] for f in bm.faces]); bm.free()
stl_write(os.path.join(OUT, TORSO + ".stl"), TT)

# the placed insert: its mesh is the file shifted by `off`; object = T R D
VI = np.array([v.co[:] for v in io.data.vertices]); TR = stl_read(U + REF); VR = TR.reshape(-1, 3)
off = VR.min(0) - VI.min(0)
A = Mi[:3, :3]; D = np.linalg.norm(A, axis=0); R = A / D
Gs = np.linalg.inv(Mt) @ Tr(Mi[:3, 3]) @ np.block([[R, np.zeros((3, 1))], [np.zeros((1, 3)), np.ones((1, 1))]]) @ Tr(-D * off)
# socket: the insert's back centre (scaled reference file coords) on the torso
lo, hi = VR.min(0), VR.max(0)
c = D * np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
o = (Gs @ np.r_[c, 1])[:3]
z = Gs[:3, :3] @ [0, 0, 1.0]; z /= np.linalg.norm(z)
y = Gs[:3, :3] @ [0, 1.0, 0]; y -= z * (y @ z); y /= np.linalg.norm(y); x = np.cross(y, z)
S = np.eye(4); S[:3, 0], S[:3, 1], S[:3, 2], S[:3, 3] = x, y, z, o
Fref = np.linalg.inv(S) @ Gs
print("Chest Insert socket at", o.round(3), "Z", z.round(3), "Y", y.round(3), "scale D", D.round(5))

sc = json.load(open("/home/claude/kitbash/library/" + T2 + ".sockets.json", encoding="utf-8"))
side = {"schemaVersion": 1, "part": "MarFil Assault - Torso 2 Insert", "category": "Chests",
        "sockets": [dict(s) for s in sc["sockets"]] + [{
            "type": "Chest Insert", "name": "MarFil Assault - Torso 2 Insert_socket_Chest Insert", "matrix": flat(S),
            "display_type": "ARROWS", "display_size": 3.0,
            "props": {"tiow_from": "Josh's insert placement in Desktop\\for inserts.blend (HH GEN3 2 on this torso): the insert's back centre, Z out along its face, Y up"}}],
        "fits": {},
        "notes": {"Chest Insert": "only this torso has the spot (Josh, Nov 9: 'The inserts will only work with this chest for now')",
                  "mesh": "Josh's cut of Mar Fil Assault Torso 2 (Desktop\\for inserts.blend), in Torso 2's file coordinates; its other sockets are Torso 2's"},
        "original": {"name": "23-Torso-2 Insert", "folder": "Chests", "path": "Desktop\\for inserts.blend"}}
for s in side["sockets"][:-1]:
    s["name"] = s["name"].replace("23-Torso-2", "MarFil Assault - Torso 2 Insert") if "23-Torso-2" in s.get("name", "") else s.get("name")
json.dump(side, open(os.path.join(OUT, TORSO + ".sockets.json"), "w", encoding="utf-8"), indent=1)

# the inserts
reg = json.load(open(REG)); made = []
for rel, r in sorted(reg.items()):
    folder, f = os.path.split(rel); n = int(os.path.splitext(f)[0])
    name = "Bits Inserts - %s %02d" % (SETS[folder], n)
    t = np.zeros(3) if rel == REF else np.array(r["A"]).reshape(4, 4)[:3, 3]   # Josh's own insert: exactly his placement
    Fi = Fref @ Tr(D * t)
    T = stl_read(U + rel) * D
    stl_write(os.path.join(OUT, INS_DIR + name + ".stl"), T)
    sd = {"schemaVersion": 1, "part": name, "category": "Chest Inserts", "fits": {"Chest Insert": flat(Fi)},
          # the files lie face up (Z out, Y up): stand them up facing +Y so the page's cards show their faces
          "upright": flat([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]),
          "notes": {"Chest Insert": "Josh's placement of HH GEN3 2 carried across by the back (shift %s mm, match median %.3f mm)" % (np.round(t, 3).tolist(), r["median"]),
                    "mesh": "the maker's file x %s (Josh's scale on his placed insert, baked in)" % D.round(5).tolist()},
          "original": {"name": os.path.splitext(f)[0], "folder": folder.replace("/", "\\"), "path": "Inserts\\" + rel.replace("/", "\\")}}
    json.dump(sd, open(os.path.join(OUT, INS_DIR + name + ".sockets.json"), "w", encoding="utf-8"), indent=1)
    made.append([INS_DIR + name + ".stl", "Inserts\\" + rel.replace("/", "\\")])
json.dump({"torso": TORSO + ".stl", "inserts": made, "S": flat(S), "Fref": flat(Fref), "D": D.tolist()}, open(os.path.join(OUT, "made.json"), "w"), indent=1)
print("inserts", len(made), "torso tris", len(TT))
