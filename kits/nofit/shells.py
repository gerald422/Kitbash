"""Shells (Josh, Nov 14, notes 094 / 095): the mating faces of ONE fitted part a maker folder (maker + armour type) and
part type, lying where that part sits on its joint, so a scene's centre is the socket and every maker's shell of a
type is in the same place. A part is then brought to the shell and mated there; the only fit set by hand is the
shell's own.

    PY  shells.py make  LIBRARY OUT [--types "Shoulder Pads,Heads,Backpacks,Arms,Hands"] [--pads WORK]
                        OUT/<maker folder> - <type> shell.stl and OUT/shells.json (which part each came from)
    BL  shells.py blend OUT FILE.blend LIBRARY [CHECKDIR]      (CHECKDIR: two pictures a scene, to look at)
                        one scene a part type: its shells at the centre, Mar Fil's body round the joint as a wire guide
  PY = a Python with numpy (Blender's own); BL = blender --background --factory-startup --python shells.py --

Which part: for pads the master `masters.py one` used (--pads WORK, its one-*.json); for Mar Fil, Josh's own reference
parts (helmet 1, arm 1A R); otherwise the fitted right-hand part whose box is the folder's most ordinary (nearest the
median). Which faces: a pad's inside (kb.carry.inner); arms and backpacks the flat face at the joint (the shoulder
disc, the mount plate: the level with most area); heads and hands the faces within RADIUS that look back into it. A left part
is mirrored first, so every shell is a right-hand one. 1 unit = 1 mm, as the library's files are.
"""
import sys, os, json, glob, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]
TYPES = ["Shoulder Pads", "Heads", "Backpacks", "Arms", "Hands"]
RADIUS = {"Heads": 4.0, "Backpacks": 8.0, "Arms": 6.0, "Hands": 3.0}
FLAT = ("Arms", "Backpacks")       # these meet their joint on a flat face (the shoulder disc, the mount plate)
OWN = {("Mar Fil - Tacticus", "Heads"): "Mar Fil - Tacticus/AssaultMarines-V2/Helmet-Heads/Heads/MarFil Assault - Helmet 1",
       ("Mar Fil - Tacticus", "Arms"): "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 1A R"}
SOCK = {"Shoulder Pads": "Pad R", "Heads": "Neck", "Backpacks": "Back", "Arms": "Shoulder R", "Hands": "Hand R"}
TORSO = "Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1"
ARM = "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 1A R"


def write_stl(path, T):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
    rec = np.zeros(len(T), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]); rec["n"], rec["v"] = n, T
    with open(path, "wb") as fo: fo.write(b"shell".ljust(80, b" ")); fo.write(np.uint32(len(T)).tobytes()); fo.write(rec.tobytes())
def move(T, M): return (np.c_[T.reshape(-1, 3), np.ones(len(T) * 3)] @ M.T)[:, :3].reshape(-1, 3, 3)


def make(lib, out, A):
    from kb import carry
    import carry_library as CL, masters as MS
    types = CL.opt(A, "--types", ",".join(TYPES)).split(","); pads = CL.opt(A, "--pads"); os.makedirs(out, exist_ok=True); done = []
    P = CL.scan(lib, types)
    for typ in types:
        by = collections.defaultdict(list)
        for rel, sc in P[typ]:
            if MS.right_fit(sc)[0] is not None: by[CL.maker(rel)].append((rel, sc))
        for mk in sorted(by):
            D = dict(by[mk]); pick, why = OWN.get((mk, typ)), "Josh's reference part"
            if typ == "Shoulder Pads" and pads and os.path.exists("%s/one-%s.json" % (pads, mk)):
                pick, why = json.load(open("%s/one-%s.json" % (pads, mk), encoding="utf-8"))["master"], "the master its pads were seated on"
            if pick not in D:
                right = [(rel, sc) for rel, sc in by[mk] if not MS.right_fit(sc)[1]] or by[mk]
                E = {}
                for rel, sc in right:
                    try: E[rel] = np.sort(np.ptp(carry.soup(lib + "/" + rel + ".stl", sc.get("scale", 1.0)).reshape(-1, 3), 0))
                    except (OSError, ValueError): pass
                if not E: continue
                med = np.median(np.array(list(E.values())), 0); pick = min(E, key=lambda r: float(np.abs(E[r] - med).sum())); why = "the most ordinary box of %d fitted" % len(E)
            sc = D[pick]; F, left = MS.right_fit(sc)
            tri = carry.soup(lib + "/" + pick + ".stl", sc.get("scale", 1.0)) * (np.array([-1.0, 1, 1]) if left else 1.0); c = tri.mean(1)
            if typ == "Shoulder Pads":
                I = carry.inner(carry.sample(tri, 60000, 0)); C = carry._centre(I); bins = 60
                def cell(Q):
                    d = Q - C; r = np.linalg.norm(d, axis=1); u = d / np.maximum(r, 1e-9)[:, None]
                    th = np.arccos(np.clip(u[:, 2], -1, 1)); ph = np.arctan2(u[:, 1], u[:, 0]) + np.pi
                    return np.minimum((th / np.pi * bins).astype(int), bins - 1) * (2 * bins) + np.minimum((ph / (2 * np.pi) * 2 * bins).astype(int), 2 * bins - 1), r
                k, r = cell(I); far = np.full(2 * bins * bins, -1.0); np.maximum.at(far, k, r); kc, rc = cell(c); keep = rc <= far[kc] + 0.15; rad = None
            else:
                # the faces that meet the joint: near it, and looking back into what the part hangs from (the socket's
                # Z points out of the joint, so their normals point against it once the part is in the socket's space)
                J = carry.point("fit", F); rad = RADIUS.get(typ, 6.0); near = np.linalg.norm(c - J, axis=1) < rad
                if near.sum() < 30: rad *= 1.6; near = np.linalg.norm(c - J, axis=1) < rad
                n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]) * (-1.0 if left else 1.0); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
                nz = (n @ F[:3, :3].T)[:, 2]; keep = near & (nz < -0.6)
                if typ in FLAT:                                              # the flat face: the level with most area
                    flat = near & (nz < -0.96)
                    if flat.sum() >= 12:
                        ar = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
                        z = (c @ F[:3, :3].T + F[:3, 3])[:, 2]; h = np.round(z[flat] / 0.2) * 0.2; vals, ix = np.unique(h, return_inverse=True)
                        keep = flat & (np.abs(z - vals[np.bincount(ix, ar[flat]).argmax()]) < 0.3)
                if keep.sum() < 30: keep = near & (nz < -0.25)
                if keep.sum() < 30: keep = near                              # normals not to be trusted: everything near
            if keep.sum() < 12: print("%-40s %-14s NO SHELL: %s has %d faces at its joint" % (mk, typ, os.path.basename(pick), keep.sum())); continue
            T = move(tri[keep], F); name = "%s - %s shell" % (mk, typ); write_stl("%s/%s.stl" % (out, name), T); v = T.reshape(-1, 3)
            done.append({"shell": name, "maker": mk, "type": typ, "socket": SOCK[typ], "from": pick, "left": left, "why": why, "faces": int(keep.sum()), "radius": rad,
                         "box": [[round(float(x), 2) for x in v.min(0)], [round(float(x), 2) for x in v.max(0)]]})
            print("%-40s %-14s %6d faces from %-48s (%s)" % (mk, typ, keep.sum(), os.path.basename(pick)[-48:], why), flush=True)
    json.dump(done, open(out + "/shells.json", "w", encoding="utf-8"), indent=1)
    print("%d shells -> %s" % (len(done), out))


def blend(out, blendfile, lib, check=None):
    import bpy
    from kb import carry
    def sidecar(rel): return json.load(open(lib + "/" + rel + ".sockets.json", encoding="utf-8-sig"))
    def sock(sc, t): return np.array(next(s["matrix"] for s in sc["sockets"] if s["type"] == t)).reshape(4, 4)
    tor, arm = sidecar(TORSO), sidecar(ARM); inv = np.linalg.inv
    Warm = sock(tor, "Shoulder R") @ np.array(arm["fits"]["Shoulder R"]).reshape(4, 4)            # the arm in the torso's space
    guide = {"Heads": [(TORSO, inv(sock(tor, "Neck")))], "Backpacks": [(TORSO, inv(sock(tor, "Back")))], "Arms": [(TORSO, inv(sock(tor, "Shoulder R")))],
             "Shoulder Pads": [(ARM, inv(sock(arm, "Pad R"))), (TORSO, inv(Warm @ sock(arm, "Pad R")))],
             "Hands": [(ARM, inv(sock(arm, "Hand R")))] if any(s["type"] == "Hand R" for s in arm["sockets"]) else []}
    def obj(scene, name, T, wire=False):
        me = bpy.data.meshes.new(name); n = len(T); me.from_pydata(T.reshape(-1, 3).tolist(), [], np.arange(n * 3).reshape(-1, 3).tolist()); me.update()
        o = bpy.data.objects.new(name, me); scene.collection.objects.link(o)
        if wire: o.display_type = "WIRE"; o.hide_select = True
        return o
    bpy.ops.wm.read_factory_settings(use_empty=True); first = bpy.context.scene; S = json.load(open(out + "/shells.json", encoding="utf-8")); made = {}
    for typ in dict.fromkeys(s["type"] for s in S):
        sc = bpy.data.scenes.new(typ); made[typ] = 0
        sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 0.001; sc.unit_settings.length_unit = "MILLIMETERS"
        for s in (s for s in S if s["type"] == typ):
            T = carry.soup("%s/%s.stl" % (out, s["shell"])); o = obj(sc, s["shell"], T); o["from"] = s["from"]; o["socket"] = s["socket"]; made[typ] += 1
        for rel, M in guide.get(typ, []):
            obj(sc, "guide " + os.path.basename(rel), move(carry.soup(lib + "/" + rel + ".stl"), M), wire=True)
    bpy.data.scenes.remove(first)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blendfile))
    print("scenes:", ", ".join("%s (%d shells)" % kv for kv in made.items()), "->", blendfile)
    if check:                                              # pictures to look at (after the save: the file keeps no camera)
        from mathutils import Matrix, Vector
        sys.path.insert(0, REPO + "/tests"); import rend
        cols = [rend.BLUE, rend.ORANGE, rend.GREEN, rend.PURPLE, rend.RED, (0.9, 0.85, 0.3, 1), (0.4, 0.8, 0.8, 1), (0.85, 0.5, 0.7, 1)]
        os.makedirs(check, exist_ok=True)
        for sc in bpy.data.scenes:
            cam = rend.setup(sc, 520); sh = [o for o in sc.objects if o.type == "MESH" and not o.name.startswith("guide")]
            for k, o in enumerate(o for o in sc.objects if o.type == "MESH"): o.color = cols[k % len(cols)] if not o.name.startswith("guide") else (0.6, 0.6, 0.58, 1)
            pts = [Vector(c) for o in sh for c in o.bound_box]; lo = Vector([min(q[i] for q in pts) for i in range(3)]); hi = Vector([max(q[i] for q in pts) for i in range(3)])
            c = (lo + hi) / 2; size = (hi - lo).length
            for vn, d, guides in (("a", (1, -1, 0.7), True), ("b", (-1, 1, -0.7), False)):
                for o in sc.objects:
                    if o.type == "MESH": o.hide_render = o.name.startswith("guide") and not guides
                d = Vector(d).normalized(); u = Vector((0, 0, 1)); y = (u - d * u.dot(d)).normalized(); x = y.cross(d)
                cam.matrix_world = Matrix.LocRotScale(c + d * (size * 3 + 50), Matrix((x, y, d)).transposed().to_quaternion(), None); cam.data.ortho_scale = size * 1.5
                sc.render.filepath = "%s/%s_%s.png" % (check, sc.name, vn); bpy.ops.render.render(write_still=True, scene=sc.name)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if not A: sys.exit(__doc__)
    if A[0] == "make": make(A[1], A[2], A)
    elif A[0] == "blend": blend(A[1], A[2], A[3], A[4] if len(A) > 4 else None)
    else: sys.exit(__doc__)
