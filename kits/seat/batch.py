"""Batch files (docs/PLAN.md, Method 2-5): build a batch for Josh to fix by eye, read what he changed, compare two files.

    BL kits/seat/batch.py -- build SPEC.json [--lib LIB] [--out BLEND] [--then SCRIPT.py]
    BL kits/seat/batch.py -- read BATCH.blend [--json OUT.json]
    BL kits/seat/batch.py -- compare A.blend B.blend
    BL kits/seat/batch.py -- write BATCH.blend [--check] [--spec SPEC.json] [--lib LIB]   (see write())
    BL kits/seat/batch.py -- apply BATCH.blend FROM_ID OUT.blend [--skip ID,ID]   (Josh's move of FROM_ID, on every piece of its kind)
  BL = blender --background --factory-startup --python   (Blender 5.1 on the PC)

build: one Blender file per batch, from a spec (kits/seat/batches/*.json). Every object is one of
  host       the approved part the batch sits on: solid, locked (can't be selected or moved)
  check      known-good pieces from the reference marine: solid, locked
  neighbour  context: solid and locked if approved, else faint; never edited
  part       what Josh fixes: free, pivoting on its joint (its origin is the joint), coloured
Parts hang in a chain (spec "parent"): moving a part moves what sits on it. Every object records where Claude put it
(kb_seated) and how its own coordinates (its library STL, or a connector's own frame) lie in the object
(kb_own_in_obj): own -> world = matrix_world @ kb_own_in_obj. A spec's objects:
  id, role, rel (library path without .stl) or connector (CONNECTORS, from a source blend), parent (an id),
  on: the frame of the parent this sits on = the pivot: a socket type of the parent's sidecar, a connector frame, or
      "self" (the object's own origin; default for hosts, checks, neighbours)
  pose: where it starts, one of
      {"from": SRC, "obj": NAME}                        that object's pose in a source blend (its mesh found in the
                                                        library file by its edge lengths, kits/connectors/reference.py)
      {"from": SRC, "obj": NAME, "relative_to": [SRC_OBJ, ID]}   kept relative to SRC_OBJ, carried onto batch object ID
      {"from": SRC, "child_of": NAME}                   the mesh child of NAME in that blend (a pad in its guide)
      {"carry": [ID, FRAME], "from": ..., "obj": ...}   kept relative to frame FRAME of ID, carried onto the pivot
      {"at_pivot": true}                                its own origin on the pivot
  preset: a change (4x4, the pivot's axes) applied after the pose: a repeated fix, shown to Josh marked "pre-set"
  mirror: true shows the left copy live (a Mirror modifier across the host torso's X = 0 plane, or across the YZ plane
          of the host's "mirror_frame" (own coordinates) when it has one: write mirrors the socket the same way)
  note: one line shown to Josh
--then SCRIPT runs a seat method (kits/seat modules) in the built scene before the seats are recorded; the script
gets `objs` (id -> object) and `spec`. The file is never written over: a batch Josh has touched is never
regenerated (PLAN, Rule 2), so a redo is a new file name.

read: opens a batch read-only and reports, per part, what Josh changed at its joint (move in mm and turn in degrees, in
the pivot's own axes, relative to the part it sits on, so a part that only rode along shows no change) and where it
now sits on its parent's frame (the number a write would store). Parts on the same joint changed the same way (within
0.2 mm and 1.5 deg) are reported as one repeated change, with its 4x4 for `preset` (PLAN, Method 4). Nothing is
written to the library: that is the write step, after Josh's fixes, with a backup.

compare: the same objects (by kb_id) in two batch files: how far apart they sit relative to the host, in mm / deg (a
batch rebuilt from the library after a write must match Josh's file)."""
import os, sys, json, math, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
from mathutils import Matrix
import geom as G

ROLES = ("host", "check", "neighbour", "part")
COLOUR = {"host": (0.62, 0.66, 0.62, 1), "check": (0.55, 0.60, 0.70, 1), "neighbour": (0.75, 0.75, 0.75, 0.25),
          "approved": (0.70, 0.70, 0.70, 1), "part": (0.90, 0.55, 0.20, 1), "preset": (0.85, 0.35, 0.75, 1), "connector": (0.90, 0.20, 0.15, 1)}
SAME_MM, SAME_DEG = 0.2, 1.5          # a repeated change: every part's change within this of the others'
MOVED_MM, MOVED_DEG = 0.01, 0.05      # below this a part counts as not changed
RZ = np.array([[0, 1.0, 0, 0], [-1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]])   # Springles frame -> Mar Fil (out +Y -> +X, front -X -> +Y)


def opt(A, n, d=None): return A[A.index(n) + 1] if n in A else d
def home(p): return os.path.expanduser(p) if isinstance(p, str) else p


# ---- connectors: printed parts with no library file, each in its own frame (docs/PLAN.md, Physical connectors)

def spacer_frame(o):
    """The Springles spacer (Josh's, ~\\Desktop\\Operation Marine\\arms.blend, where the Springles arms sit on the origin
    with their shoulder flat facing -Y): own frame = Mar Fil axes (+X out of the torso, +Y front, +Z up), origin = the
    centre of its torso face. Frames: 'torso face' (the origin) and 'arm seat' (the file's origin = where the arms' flat
    sits; the spacer goes into the arm past it). Returns (mesh local -> own 4x4, frames)."""
    W = G.verts_world(o); cx, cz = (W[:, 0].min() + W[:, 0].max()) / 2, (W[:, 2].min() + W[:, 2].max()) / 2
    T = np.eye(4); T[:3, 3] = -np.array([cx, W[:, 1].min(), cz]); C = RZ @ T          # arms.blend world -> own
    seat = np.eye(4); seat[:3, 3] = (C @ np.r_[0, 0, 0, 1.0])[:3]
    return C @ np.array(o.matrix_world), {"torso face": np.eye(4), "arm seat": seat}


def guide_frame(o):
    """The pauldron guide (the pad connector): own frame = its mesh's (origin on its crown, +Z out, +Y front)"""
    return np.eye(4), {"crown": np.eye(4)}


CONNECTORS = {"spacer": spacer_frame, "guide": guide_frame}       # spec: "connector": {"kind", "from", "obj"}


# ---- source blends (read only)

class Sources:
    def __init__(self, files, lib):
        self.files = {k: home(v) for k, v in files.items()}; self.lib = lib; self.got = {}
        self.tmp = bpy.data.collections.new("kb sources (removed before saving)"); bpy.context.scene.collection.children.link(self.tmp)

    def obj(self, src, name):
        """an object of a source blend, appended with its parents (so its matrix_world is the file's)"""
        if (src, name) in self.got: return self.got[(src, name)]
        path = self.files[src]
        with bpy.data.libraries.load(path, link=False) as (a, b):
            if name not in a.objects: raise KeyError("%r is not in %s" % (name, os.path.basename(path)))
            b.objects = [name]
        o = b.objects[0]; chain = [o]
        while chain[-1].parent is not None: chain.append(chain[-1].parent)
        for c in chain:
            if c.name not in self.tmp.objects: self.tmp.objects.link(c)
        bpy.context.view_layer.update()            # appended objects' matrix_world is stale until evaluated (notes 120)
        self.got[(src, name)] = o; return o

    def child_of(self, src, name):
        """the mesh child of `name` in that blend (appended with it)"""
        import re
        path = self.files[src]
        with bpy.data.libraries.load(path, link=False) as (a, b): b.objects = [k for k in a.objects if "(in adapter" in k]
        for o in b.objects:
            if o is not None and o.type == 'MESH' and o.parent is not None and re.sub(r"\.\d{3}$", "", o.parent.name) == name:
                for c in (o, o.parent):
                    if c.name not in self.tmp.objects: self.tmp.objects.link(c)
                bpy.context.view_layer.update(); return o
        raise KeyError("no mesh child of %r in %s" % (name, os.path.basename(path)))

    def done(self):
        for o in list(self.tmp.objects): bpy.data.objects.remove(o)
        bpy.data.collections.remove(self.tmp)
        for m in [m for m in bpy.data.meshes if m.users == 0]: bpy.data.meshes.remove(m)


def sidecar(lib, rel):
    p = os.path.join(lib, rel + ".sockets.json")
    return json.load(open(p, encoding="utf-8-sig")) if os.path.exists(p) else {}


def stl_tris(lib, rel, sc):
    from kb import connect as C
    return C.soup(os.path.join(lib, rel + ".stl"), float(sc.get("scale") or 1.0))


def own_world(src_obj, rel=None, lib=None, sc=None, conn=None):
    """own coordinates -> world of a source object: a library part's STL found in its mesh (reference.frame_of), or a
    connector's own frame"""
    mw = np.array(src_obj.matrix_world)
    if conn: C, _ = conn(src_obj); return mw @ np.linalg.inv(C)
    import reference as RF
    M = RF.frame_of(G.tris(src_obj), stl_tris(lib, rel, sc))
    if M is None: raise ValueError("%r: its mesh is not %s" % (src_obj.name, rel))
    return mw @ np.linalg.inv(M)


def make_mesh(name, tris_own, K):
    """a mesh object from triangles in own coordinates, stored as K @ own (own -> object = K, so own -> world =
    matrix_world @ K). Was K^-1 until Nov 24: right only when K is its own inverse (the arm), the pad sat 2.7 mm off."""
    V = tris_own.reshape(-1, 3) @ K[:3, :3].T + K[:3, 3]
    key = np.round(V, 6); uniq, inv = np.unique(key, axis=0, return_inverse=True)
    me = bpy.data.meshes.new(name); me.from_pydata(uniq.tolist(), [], inv.reshape(-1, 3).tolist()); me.update()
    return bpy.data.objects.new(name, me)


def lock(o, on=True):
    o.lock_location = o.lock_rotation = o.lock_scale = (on, on, on); o.lock_rotation_w = on; o.hide_select = on


# ---- build

def build(A):
    spec_path = A[1]; spec = json.load(open(spec_path, encoding="utf-8"))
    lib = opt(A, "--lib", spec.get("lib", "D:/Kitbash Library")); out = home(opt(A, "--out", spec.get("out")))
    if not out: raise SystemExit("no --out and no 'out' in the spec")
    if os.path.exists(out): raise SystemExit("%s exists: a batch file is never written over (PLAN, Rule 2); give the redo a new name" % out)
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    S = Sources(spec.get("sources", {}), lib); objs, info, frames = {}, {}, {}
    if "unit_scale" in spec: bpy.context.scene.unit_settings.scale_length = float(spec["unit_scale"])
    root = bpy.data.collections.new(spec["name"][:60]); bpy.context.scene.collection.children.link(root)
    colls = {}
    for r in ROLES:
        c = bpy.data.collections.new({"host": "HOST (locked)", "check": "CHECK PIECES (locked)", "neighbour": "NEIGHBOURS (context, never edited)", "part": "FIX THESE (move by eye, then save)"}[r])
        root.children.link(c); colls[r] = c
    log = []
    ids = [e["id"] for e in spec["objects"]]
    if len(ids) != len(set(ids)): raise SystemExit("ids used twice: %s" % sorted({i for i in ids if ids.count(i) > 1}))
    for e in spec["objects"]:
        i, role = e["id"], e["role"]; assert role in ROLES, role
        pose = e.get("pose", {}); conn = entry_conn(e)
        rel = e.get("rel"); sc = sidecar(lib, rel) if rel else {}
        # own triangles and own frames
        if conn:
            src_c = S.obj(e["connector"]["from"], e["connector"]["obj"]); C, fr = conn(src_c)
            own_tris = G.tris(src_c) @ C[:3, :3].T + C[:3, 3]
        else:
            own_tris = stl_tris(lib, rel, sc)
            fr = {s["type"]: G.M4(s["matrix"]) for s in sc.get("sockets") or []}
        fr["self"] = np.eye(4); frames[i] = fr
        # where it starts (own -> world)
        par = e.get("parent"); Wp = info[par]["W"] if par else None
        on = e.get("on", "self" if role != "part" or not par else None)
        if on is None: raise SystemExit("%s: a part with a parent needs 'on' (the parent's frame it sits on)" % i)
        on_M = G.M4(e["on_matrix"]) if e.get("on_matrix") else (frames[par][on] if par and on != "self" else None)
        piv_parent = (Wp @ on_M) if (par and on != "self") else None
        if pose.get("at_pivot"):
            W = piv_parent.copy()
            if pose.get("shift_from"):                   # a connector's own frame in a written socket (props.kb_connectors)
                r3, t3 = pose["shift_from"]; s3 = next(s for s in sidecar(lib, r3)["sockets"] if s["type"] == t3)
                W = W @ G.M4(s3["props"]["kb_connectors"][0]["own_in_socket"])
        elif "fit" in pose: W = piv_parent @ G.M4(sc["fits"][pose["fit"]])      # the part's own library fit on the pivot
        elif pose.get("place"): W = np.eye(4)                                     # its library frame
        elif "matrix" in pose: W = G.M4(pose["matrix"])                           # given own -> world (e.g. stood on its waist)
        elif "obj" in pose or "child_of" in pose:
            so = S.child_of(pose["from"], pose["child_of"]) if "child_of" in pose else S.obj(pose["from"], pose["obj"])
            W = own_world(so, rel, lib, sc, conn); e["_src"] = so.name
            if "relative_to" in pose:                    # kept relative to a source object, carried onto batch object i2
                so2, i2 = pose["relative_to"]; e2 = entry(spec, i2); r2 = e2.get("rel")
                W2 = own_world(S.obj(pose["from"], so2), r2, lib, sidecar(lib, r2) if r2 else {}, entry_conn(e2))
                W = info[i2]["W"] @ np.linalg.inv(W2) @ W
            if "carry" in pose:                          # kept relative to a frame of i3, carried onto the pivot
                i3, f3 = pose["carry"]; W = piv_parent @ np.linalg.inv(info[i3]["W"] @ frames[i3][f3]) @ W
        else: raise SystemExit("%s: no pose" % i)
        if e.get("at") and not par: T = np.eye(4); T[:3, 3] = e["at"]; W = T @ W            # a column of its own
        P = piv_parent if piv_parent is not None else W.copy()                           # the pivot (object origin)
        if e.get("preset"): D = G.M4(e["preset"]); W = P @ D @ np.linalg.inv(P) @ W; P = P @ D
        K = np.linalg.inv(P) @ W
        o = make_mesh(e.get("name", i)[:63], own_tris, K)
        if e.get("collection"):                      # its own collection Josh can hide (e.g. the second cloak style)
            if e["collection"] not in colls: c = bpy.data.collections.new(e["collection"][:60]); root.children.link(c); colls[e["collection"]] = c
            colls[e["collection"]].objects.link(o)
        else: colls[role].objects.link(o)
        o.rotation_mode = 'QUATERNION'     # Euler near gimbal lock (a file lying Y up, stood up) lost up to 0.5 deg (Nov 24)
        if par: o.parent = objs[par]; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = G.mat(np.linalg.inv(info[par]["P"]) @ P)
        else: o.matrix_world = G.mat(P)
        bpy.context.view_layer.update()
        approved = role == "neighbour" and e.get("approved")
        o.color = COLOUR["preset" if e.get("preset") else "approved" if approved else "connector" if (conn and role == "part") else role]
        if "colour" in e: o.color = tuple(e["colour"])
        lock(o, role != "part")
        o["kb_id"] = i; o["kb_role"] = role; o["kb_rel"] = rel or "connector: " + e["connector"]["kind"]
        o["kb_parent"] = par or ""; o["kb_on"] = on; o["kb_on_frame"] = G.flat16(on_M) if par and on != "self" else G.flat16(np.eye(4))
        o["kb_own_in_obj"] = G.flat16(K); o["kb_frames"] = json.dumps({k: G.flat16(v) for k, v in fr.items() if k != "self"})
        o["kb_joint"] = e.get("joint", ""); o["kb_note"] = e.get("note", ""); o["kb_preset"] = bool(e.get("preset"))
        o["kb_from"] = json.dumps(pose)
        objs[i] = o; info[i] = dict(W=W, P=P)
        log.append("%-10s %-9s %s%s" % (i, role, o.name, "  (pre-set)" if e.get("preset") else ""))
    def host_of(i):                                  # the host this hangs from (its own column's torso)
        while entry(spec, i)["role"] != "host" and entry(spec, i).get("parent"): i = entry(spec, i)["parent"]
        return objs[i] if entry(spec, i)["role"] == "host" else None
    planes = {}                                      # a host's mirror plane: its "mirror_frame" (own coordinates; YZ plane), else X = 0
    for e in spec["objects"]:
        if e["role"] == "host" and e.get("mirror_frame"):
            m = bpy.data.objects.new(e.get("name", e["id"])[:50] + " mirror plane", None); colls["host"].objects.link(m)
            m.rotation_mode = 'QUATERNION'; m.parent = objs[e["id"]]; m.matrix_parent_inverse = Matrix.Identity(4); m.matrix_basis = G.mat(G.M4(e["mirror_frame"]))
            m.empty_display_size = 3; m.hide_select = True; lock(m, True); planes[e["id"]] = m
    for e in spec["objects"]:
        torso = host_of(e["id"])
        if e.get("mirror") and torso is not None:
            import mirror; mirror.mirror_live(objs[e["id"]], planes.get(torso["kb_id"], torso))
    S.done()
    for e in spec["objects"]: objs[e["id"]].name = e.get("name", e["id"])[:63]     # the source copies held the names
    then = opt(A, "--then")
    if then:
        exec(compile(open(then, encoding="utf-8").read(), then, "exec"), dict(objs=objs, spec=spec, bpy=bpy, np=np, G=G, __name__="kb_then"))
        bpy.context.view_layer.update()
    for i, o in objs.items(): o["kb_seated"] = G.flat16(np.array(o.matrix_world))     # where Claude put it
    bpy.context.view_layer.update()
    readme(spec, objs)
    viewport()
    meta = dict(name=spec["name"], stage=spec.get("stage"), spec=os.path.basename(spec_path), built=time.strftime("%Y-%m-%d %H:%M"), lib=lib)
    bpy.context.scene["kb_batch"] = json.dumps(meta)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out, check_existing=True, compress=True)
    print("\n".join(log)); print("SAVED", out, flush=True)


def entry(spec, i): return next(e for e in spec["objects"] if e["id"] == i)
def entry_conn(e): return CONNECTORS[e["connector"]["kind"]] if e.get("connector") else None


def readme(spec, objs):
    t = bpy.data.texts.new("READ ME - this batch")
    L = ["%s (stage %s)" % (spec["name"], spec.get("stage", "?")), "", spec.get("about", ""), "",
         "FIX THESE: move / turn each by eye (its origin is its joint, so it turns about the joint), then save this file.",
         "Whatever sits on a part moves with it. Locked pieces can't be selected: they are the approved host and the",
         "known-good check pieces. Faint pieces are context only. Don't rename objects (they are read back by name and kb_id).", ""]
    for e in spec["objects"]:
        if e["role"] == "part": L.append("- %s%s: %s" % (objs[e["id"]].name, " (PRE-SET: a repeated fix applied)" if e.get("preset") else "", e.get("note", "")))
    t.write("\n".join(L) + "\n")


def viewport():
    for scr in bpy.data.screens:
        for a in scr.areas:
            if a.type != 'VIEW_3D': continue
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.shading.type = 'SOLID'; s.shading.color_type = 'OBJECT'; s.shading.show_cavity = True
                    s.clip_start = 0.1; s.clip_end = 10000


# ---- read

def joint_rel(o):
    """(the object's pose on its parent now, at build): object -> parent object, 4x4"""
    p = o.parent
    now = np.array(o.matrix_world); seated = G.M4(o["kb_seated"])
    if p is None: return now, seated
    return np.linalg.inv(np.array(p.matrix_world)) @ now, np.linalg.inv(G.M4(p["kb_seated"])) @ seated


def change(D):
    """a change (4x4, pivot axes): move mm (x, y, z), turn deg, turn axis"""
    t = D[:3, 3]; a = G.ang(np.eye(4), D); R = D[:3, :3]
    ax = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]); n = np.linalg.norm(ax)
    return dict(move_mm=[round(float(x), 3) for x in t], move_len=round(float(np.linalg.norm(t)), 3), turn_deg=round(a, 2),
                turn_axis=[round(float(x), 3) for x in (ax / n if n > 1e-9 else ax)])


def read(A):
    blend = A[1]; out = opt(A, "--json")
    bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False); bpy.context.view_layer.update()
    meta = json.loads(bpy.context.scene.get("kb_batch", "{}"))
    objs = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    rows, lost = [], [o.name for o in bpy.data.objects if o.type == 'MESH' and "kb_id" not in o]
    for i, o in objs.items():
        now, seated = joint_rel(o); D = np.linalg.inv(seated) @ now; ch = change(D)
        moved = ch["move_len"] > MOVED_MM or ch["turn_deg"] > MOVED_DEG
        own = np.array(o.matrix_world) @ G.M4(o["kb_own_in_obj"]); r = dict(id=i, name=o.name, role=o["kb_role"], rel=o["kb_rel"], joint=o.get("kb_joint", ""),
                                                                           changed=moved, change=ch, D=G.flat16(D), preset=bool(o.get("kb_preset")))
        if o.parent is not None:
            p = o.parent; Wp = np.array(p.matrix_world) @ G.M4(p["kb_own_in_obj"])
            r["on"] = o["kb_on"]; r["parent"] = p["kb_id"]
            r["in_parent_own"] = G.flat16(np.linalg.inv(Wp) @ own)                            # own -> parent's own coordinates
            r["on_frame"] = G.flat16(np.linalg.inv(Wp @ G.M4(o["kb_on_frame"])) @ own)        # own -> the parent frame it sits on
        if o["kb_role"] != "part" and moved: r["warning"] = "a locked piece moved: not used"
        rows.append(r)
    groups = {}
    for r in rows:
        if r["role"] == "part" and r["joint"]: groups.setdefault(r["joint"], []).append(r)
    repeated = []
    for j, rs in groups.items():
        ch = [r for r in rs if r["changed"]]
        if len(rs) < 2 or len(ch) < 2: continue
        Ds = [G.M4(r["D"]) for r in ch]; ref = Ds[0]
        same = all(np.linalg.norm(D[:3, 3] - ref[:3, 3]) <= SAME_MM and G.ang(ref, D) <= SAME_DEG for D in Ds)
        turn_same = all(G.ang(ref, D) <= SAME_DEG for D in Ds)
        avg = np.eye(4); avg[:3, 3] = np.mean([D[:3, 3] for D in Ds], 0)
        U, _, Vt = np.linalg.svd(sum(D[:3, :3] for D in Ds)); avg[:3, :3] = U @ np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))]) @ Vt
        repeated.append(dict(joint=j, parts=len(rs), changed=len(ch), same=same, same_turn_only=turn_same and not same,
                             unchanged=[r["id"] for r in rs if not r["changed"]], preset=G.flat16(avg) if same or turn_same else None, change=change(avg)))
    res = dict(batch=meta, file=os.path.basename(blend), read=time.strftime("%Y-%m-%d %H:%M"), rows=rows, repeated=repeated, not_from_the_batch=lost)
    W = ["Batch read: %s (%s)" % (meta.get("name", "?"), os.path.basename(blend)), ""]
    for r in rows:
        if r["role"] != "part" and not r.get("warning"): continue
        c = r["change"]
        W.append("%-10s %-44s %s" % (r["id"], r["name"][:44], ("CHANGED: move %.2f mm (x %.2f y %.2f z %.2f), turn %.2f deg about (%.2f %.2f %.2f)"
                 % (c["move_len"], *c["move_mm"], c["turn_deg"], *c["turn_axis"])) if r["changed"] else "unchanged") + ("  " + r["warning"] if r.get("warning") else ""))
    for g in repeated:
        W.append("Repeated on %r: %d of %d parts changed, %s" % (g["joint"], g["changed"], g["parts"], "the SAME change" if g["same"] else "the same turn only" if g["same_turn_only"] else "not the same"))
    if lost: W.append("Meshes not from the batch (not read): " + ", ".join(lost[:10]))
    print("\n".join(W), flush=True)
    if out: json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
    return res


# ---- compare

def compare(A):
    a, b = A[1], A[2]; poses = []
    for f in (a, b):
        bpy.ops.wm.open_mainfile(filepath=f, load_ui=False); bpy.context.view_layer.update()
        host = next((o for o in bpy.data.objects if o.get("kb_role") == "host"), None)
        Hi = np.linalg.inv(np.array(host.matrix_world) @ G.M4(host["kb_own_in_obj"])) if host else np.eye(4)
        poses.append({o["kb_id"]: Hi @ np.array(o.matrix_world) @ G.M4(o["kb_own_in_obj"]) for o in bpy.data.objects if "kb_id" in o})
    W = ["Compare %s / %s (own coordinates, relative to the host)" % (os.path.basename(a), os.path.basename(b))]
    for i in sorted(set(poses[0]) | set(poses[1])):
        if i not in poses[0] or i not in poses[1]: W.append("%-10s only in %s" % (i, os.path.basename(a if i in poses[0] else b))); continue
        P, Q = poses[0][i], poses[1][i]; d = float(np.linalg.norm(P[:3, 3] - Q[:3, 3])); t = G.ang(P, Q)
        W.append("%-10s %7.3f mm %6.2f deg %s" % (i, d, t, "MATCH" if d < 0.01 and t < 0.05 else "differs"))
    print("\n".join(W), flush=True)


# ---- write (PLAN Method 5 and Rule 1): Josh's placements in a batch file -> the library, backup first

MX = np.diag([-1.0, 1, 1, 1])          # the left side: the right one conjugated by the X = 0 mirror (as the batch shows it)


def own(o): return np.array(o.matrix_world) @ G.M4(o["kb_own_in_obj"])


def joint_of(objs, part, host):
    """A part's joint on its host, collapsing the connectors in between (TIOW places part = socket . fit; a printed
    connector has no library file): socket = host own -> the frame the part sits on; fit = that frame -> part own;
    each connector's own frame in the socket frame."""
    o = objs[part]; J = own(o.parent) @ G.M4(o["kb_on_frame"]); c = o.parent; conns = []
    while c["kb_id"] != host:
        if not c["kb_rel"].startswith("connector"): raise SystemExit("%s: %s sits between it and %s and is not a connector" % (part, c.name, host))
        conns.append(c); c = c.parent
        if c is None: raise SystemExit("%s does not hang on %s" % (part, host))
    S = np.linalg.inv(own(objs[host])) @ J; F = np.linalg.inv(J) @ own(o)
    con = [(c["kb_rel"].split(": ", 1)[1], c.name, np.linalg.inv(J) @ own(c)) for c in conns]
    return S, F, con


def _socket(old_socks, typ, M, props, stem):
    old = next((s for s in old_socks or [] if s.get("type") == typ), None)
    s = {k: v for k, v in (old or {}).items() if k not in ("matrix", "props", "points")}
    s.setdefault("type", typ); s.setdefault("name", "%s_socket_%s" % (stem, typ))
    s["matrix"] = G.flat16(M); s["props"] = props; return s


def _mirror_variant(d):
    return next((v for v in d.get("variants") or [] if v.get("side") == "L" and v.get("mirror")), None)


def _diff(old, new):
    if old is None: return "new"
    A, B = G.M4(old), G.M4(new); return "%.3f mm %.2f deg from the old one" % (np.linalg.norm(A[:3, 3] - B[:3, 3]), G.ang(A, B))


def write(A):
    """write BATCH.blend [--check]: every spec part with "write": {"host", "socket", "mirror"} gets its joint written:
    the host's socket (and the mirror socket: top level if the host has one, else in its mirrored L variant), the part's
    fit (and the mirror fit in its mirrored L variant). Sockets are marked props.kb_josh (kb.sidecar keeps them from then
    on) and fits go in "exact" (merge keeps those). Backs up first, writes the library and the repo's mirror, then
    places every written joint the way TIOW does (socket . fit) and checks it against Josh's file."""
    from kb import sidecar as SC
    blend = A[1]; check = "--check" in A
    res = read(["read", blend])                       # opens the file
    meta = json.loads(bpy.context.scene.get("kb_batch", "{}"))
    spec = json.load(open(opt(A, "--spec", os.path.join(HERE, "batches", meta["spec"])), encoding="utf-8"))
    lib = opt(A, "--lib", meta.get("lib", "D:/Kitbash Library")); objs = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    bad = [r["name"] for r in res["rows"] if r.get("warning")]
    if bad: raise SystemExit("locked pieces moved, nothing written: " + ", ".join(bad))
    tag = "Josh's fix in batch '%s' (kits/seat/batch.py write, %s)" % (os.path.splitext(os.path.basename(blend))[0], time.strftime("%Y-%m-%d"))
    new, olds, W, checks = {}, {}, [""], []

    def get(rel):
        if rel not in olds: olds[rel] = SC.load(os.path.join(lib, rel + SC.SUFFIX)); new[rel] = {}
        return olds[rel][0], new[rel]

    for e in spec["objects"]:
        w = e.get("write")
        if not w: continue
        if e["id"] not in objs:              # Josh removed it from the file (Nov 25: cloaks he isn't keeping): nothing written
            W.append("%-24s (removed from the file by Josh: not written)" % e["name"][-24:]); continue
        half = w.get("half", "both")      # "socket": the part and its fit are known-good, so its move is the host's socket;
        o = objs[e["id"]]; h = entry(spec, w["host"]); hrel = h["rel"]   # "fit": the socket is, so its move is the fit
        S, F, con = joint_of(objs, e["id"], w["host"])
        if half == "socket":
            if o.parent is not objs[w["host"]]: raise SystemExit("%s: a socket write needs it straight on %s" % (e["id"], w["host"]))
            S = np.linalg.inv(own(objs[w["host"]])) @ np.array(o.matrix_world)            # its pivot = the socket
            con = [(e["connector"]["kind"], o.name, np.linalg.inv(np.array(o.matrix_world)) @ own(o))] if e.get("connector") else []
        props = lambda M, cn: {"tiow_from": tag, "kb_josh": os.path.basename(blend),
                               "kb_connectors": [{"kind": k, "name": n, "own_in_socket": G.flat16(M @ C @ M)} for k, n, C in cn]}
        hd, hn = get(hrel); stem = hd.get("part") or os.path.basename(hrel); m = w.get("mirror")
        if half != "fit":
            old = next((s["matrix"] for s in hd.get("sockets") or [] if s["type"] == w["socket"]), None)
            hn.setdefault("sockets", []).append(_socket(hd.get("sockets"), w["socket"], S, props(np.eye(4), con), stem))
            W.append("%-24s socket %-10s %s" % (os.path.basename(hrel)[-24:], w["socket"], _diff(old, G.flat16(S))))
            Fm = G.M4(h["mirror_frame"]) if h.get("mirror_frame") else np.eye(4)      # the host's mirror plane (as the batch shows it)
            SL = Fm @ MX @ np.linalg.inv(Fm) @ S @ MX
            if m and (any(s["type"] == m for s in hd.get("sockets") or []) or not _mirror_variant(hd)):   # top level (also a
                old = next((s["matrix"] for s in hd.get("sockets") or [] if s["type"] == m), None)        # host with none yet)
                hn.setdefault("sockets", []).append(_socket(hd.get("sockets"), m, SL, props(MX, con), stem))
                W.append("%-24s socket %-10s %s (mirror)" % (os.path.basename(hrel)[-24:], m, _diff(old, G.flat16(SL))))
            elif m and _mirror_variant(hd):
                v = _mirror_variant(hd); vs = (v.get("sidecar") or {}).get("sockets") or []
                old = next((s["matrix"] for s in vs if s["type"] == m), None)
                hn.setdefault("variants", []).append({"name": v["name"], "side": "L", "sidecar": {"sockets": [_socket(vs, m, SL, props(MX, con), v["name"])]}})
                W.append("%-24s socket %-10s %s (mirror, in variant %s)" % (os.path.basename(hrel)[-24:], m, _diff(old, G.flat16(SL)), v["name"]))
        k = 1.0
        if half != "socket":
            prel = e["rel"]; pd, pn = get(prel)
            sv = np.linalg.svd(F[:3, :3], compute_uv=False); k = float(np.cbrt(np.linalg.det(F[:3, :3])))
            if abs(k - 1) > 1e-4:            # Josh scaled the part (Nov 25, two cloaks): the part's own scale, the fit rigid
                if sv.max() - sv.min() > 1e-4 * k: raise SystemExit("%s: scaled unevenly %s, not written" % (e["id"], np.round(sv, 4)))
                if m: raise SystemExit("%s: a scaled part with a mirror fit is not handled, not written" % e["id"])
                k0 = float(pd.get("scale") or 1.0); F = F @ np.diag([1 / k, 1 / k, 1 / k, 1]); pn["scale"] = round(k0 * k, 6)
                W.append("%-24s scale  %.4f -> %.4f (Josh scaled it %.2f%%)" % (os.path.basename(prel)[-24:], k0, k0 * k, 100 * k))
            FL = MX @ F @ MX
            oldf = (pd.get("fits") or {}).get(w["socket"])
            pn.setdefault("fits", {})[w["socket"]] = G.flat16(F); pn.setdefault("exact", []).append(w["socket"])
            pn.setdefault("notes", {})[w["socket"]] = tag
            W.append("%-24s fit    %-10s %s" % (os.path.basename(prel)[-24:], w["socket"], _diff(oldf, G.flat16(F))))
            others = [t for t in pd.get("fits") or {} if t != w["socket"]]
            if others: W.append("             (its other fits stay: %s)" % ", ".join(others))
            if m and _mirror_variant(pd):
                v = _mirror_variant(pd); oldf = ((v.get("sidecar") or {}).get("fits") or {}).get(m)
                pn.setdefault("variants", []).append({"name": v["name"], "side": "L", "sidecar": {"fits": {m: G.flat16(FL)}, "exact": [m], "notes": {m: tag}}})
                W.append("%-24s fit    %-10s %s (mirror, in variant %s)" % (os.path.basename(prel)[-24:], m, _diff(oldf, G.flat16(FL)), v["name"]))
        checks.append((e["id"], w, hrel, e.get("rel"), np.linalg.inv(own(objs[w["host"]])) @ own(o) @ np.diag([1 / k, 1 / k, 1 / k, 1])))
    out, types = {}, set(json.load(open(os.path.join(REPO, "joints.json"), encoding="utf-8"))["partTypes"])
    for n in new.values():                           # one entry per variant (an arm is host of Pad L and part on Shoulder L)
        vs = {}
        for v in n.get("variants") or []:
            k = (v["name"], v["side"])
            if k not in vs: vs[k] = v; continue
            a, b = vs[k]["sidecar"], v["sidecar"]
            a.setdefault("sockets", []).extend(b.get("sockets") or []); a.setdefault("fits", {}).update(b.get("fits") or {})
            a.setdefault("exact", []).extend(b.get("exact") or []); a.setdefault("notes", {}).update(b.get("notes") or {})
        if "variants" in n: n["variants"] = list(vs.values())
    redo = {}                                        # Josh redoing his own written socket (Nov 25, the TN legs; notes 142):
    for e in spec["objects"]:                        # only a write marked "redo" in the spec may replace a kb_josh socket
        w = e.get("write") or {}
        if w.get("redo") and e["id"] in objs: redo.setdefault(entry(spec, w["host"])["rel"], set()).add(w["socket"])
    for rel, n in new.items():
        base = olds[rel][0]
        if rel in redo:
            base = json.loads(json.dumps(base))
            for s in base.get("sockets") or []:
                p = s.get("props") or {}
                if s.get("type") in redo[rel] and p.get("kb_josh"):
                    W.append("%-24s socket %-10s redo: Josh's earlier fix (%s) replaced" % (os.path.basename(rel)[-24:], s["type"], p["kb_josh"]))
                    del p["kb_josh"]
        merged, kept = SC.merge(n, base)
        if kept: raise SystemExit("%s: already Josh's / protected, not written (Rule 1): %s" % (rel, kept))
        p = [x for x in SC.problems(merged, types) if x not in SC.problems(olds[rel][0], types)]   # only new problems
        if p: raise SystemExit("%s: %s" % (rel, p))
        out[rel] = merged
    print("\n".join(W), flush=True)
    if check: print("\n--check: nothing written", flush=True); return
    task = "batch write %s" % time.strftime("%Y-%m-%d %H%M"); B = os.path.join(lib, "_backups", task, "before", "lib")
    for rel, d in out.items():
        src = os.path.join(lib, rel + SC.SUFFIX); dst = os.path.join(B, rel + SC.SUFFIX); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(open(src, "rb").read())
    for rel, d in out.items():
        repo_p = os.path.join(REPO, "library", rel + SC.SUFFIX); src = os.path.join(lib, rel + SC.SUFFIX)
        in_step = os.path.exists(repo_p) and open(repo_p, "rb").read() == open(src, "rb").read()
        data = SC.save(src, d, olds[rel][1])
        if in_step: open(repo_p, "wb").write(data)
        else: print("NOTE: the repo copy of %s was not the same as the library's, so it was left alone" % rel)
    print("\nwritten %d sidecar(s); old copies in %s" % (len(out), B), flush=True)
    # placed the TIOW way from what is now on disk, against Josh's file
    W = ["", "Check: each written joint placed from the library (socket . fit) against Josh's file:"]
    for i, w, hrel, prel, want in checks:
        hd = SC.load(os.path.join(lib, hrel + SC.SUFFIX))[0]; s = next(s for s in hd["sockets"] if s["type"] == w["socket"])
        S = G.M4(s["matrix"])
        if prel: F = G.M4(SC.load(os.path.join(lib, prel + SC.SUFFIX))[0]["fits"][w["socket"]])
        else: F = G.M4(s["props"]["kb_connectors"][0]["own_in_socket"])        # a connector straight on the socket
        got = S @ F; W.append("%-8s on %-10s %.4f mm %.3f deg" % (i, w["socket"], np.linalg.norm(got[:3, 3] - want[:3, 3]), G.ang(got, want)))
    print("\n".join(W), flush=True)


def apply(A):
    """apply BATCH.blend FROM_ID[,FROM_ID...] OUT.blend [--into OTHER.blend] [--skip ID,ID]: Josh's change to piece FROM_ID (e.g. t1_legs), in the frame it sits on (its
    socket, so the same on every torso: they stand on the same sockets), put on every other piece of the same kind
    (same id suffix, reference column left alone). Josh's file is not touched: the result is saved as OUT, a new file,
    for him to check; read / write treat the applied moves like his own (notes 129)."""
    src, fids, out = A[1], A[2].split(","), A[3]      # several FROM_IDs: one per kind (e.g. t1_cloak,t1_cloak2, Nov 25)
    into = opt(A, "--into")                          # another batch file of the same kind to apply them in (Nov 25)
    if os.path.exists(out): raise SystemExit("%s exists: never overwritten" % out)
    def load(p):
        bpy.ops.wm.open_mainfile(filepath=p, load_ui=False); bpy.context.view_layer.update()
        return {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    by = load(src)
    def in_frame(o):                                 # the piece's pivot in the frame it sits on (the parent's frame)
        par = by[o["kb_parent"]]; return np.linalg.inv(own(par) @ G.M4(o["kb_on_frame"])) @ np.array(o.matrix_world)
    Ds = {}
    for fid in fids:
        Ds[fid.split("_", 1)[1]] = (fid, in_frame(by[fid]))
        print("%s: %.3f mm %.2f deg in its socket frame" % ((fid,) + tuple(G.off(Ds[fid.split("_", 1)[1]][1], np.eye(4)))))
    if into: by = load(into)
    skip = set((opt(A, "--skip", "") or "").split(",")); done = []
    for i, o in by.items():
        if "_" not in i or i.startswith("ref") or i in skip or i.split("_", 1)[1] not in Ds: continue
        fid, D = Ds[i.split("_", 1)[1]]
        if i == fid and not into: continue
        par = by[o["kb_parent"]]; o.rotation_mode = 'QUATERNION'
        o.matrix_world = G.mat(own(par) @ G.M4(o["kb_on_frame"]) @ D); o["kb_applied"] = "%s's change (%s)" % (fid, os.path.basename(src))
        done.append(i)
    bpy.context.view_layer.update()
    worst = max([sum(G.off(in_frame(by[i]), Ds[i.split("_", 1)[1]][1])) for i in done] or [0])
    print("applied to %d: %s (worst %.5f mm+deg off)" % (len(done), " ".join(done), worst))
    bpy.ops.wm.save_as_mainfile(filepath=out); print("SAVED", out)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        {"build": build, "read": read, "compare": compare, "write": write, "apply": apply}[A[0]](A)
    except SystemExit as e:
        print("STOPPED:", e, flush=True)
    sys.stdout.flush(); os._exit(0)
