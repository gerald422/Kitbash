"""Batch files (docs/PLAN.md, Method 2-5): build a batch for Josh to fix by eye, read what he changed, compare two files.

    BL kits/seat/batch.py -- build SPEC.json [--lib LIB] [--out BLEND] [--then SCRIPT.py]
    BL kits/seat/batch.py -- read BATCH.blend [--json OUT.json]
    BL kits/seat/batch.py -- compare A.blend B.blend
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
  mirror: true shows the left copy live (a Mirror modifier across the host torso's X = 0 plane)
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
        piv_parent = (Wp @ frames[par][on]) if (par and on != "self") else None
        if pose.get("at_pivot"): W = piv_parent.copy()
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
        P = piv_parent if piv_parent is not None else W.copy()                           # the pivot (object origin)
        if e.get("preset"): D = G.M4(e["preset"]); W = P @ D @ np.linalg.inv(P) @ W; P = P @ D
        K = np.linalg.inv(P) @ W
        o = make_mesh(e.get("name", i)[:63], own_tris, K); colls[role].objects.link(o)
        if par: o.parent = objs[par]; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = G.mat(np.linalg.inv(info[par]["P"]) @ P)
        else: o.matrix_world = G.mat(P)
        bpy.context.view_layer.update()
        approved = role == "neighbour" and e.get("approved")
        o.color = COLOUR["preset" if e.get("preset") else "approved" if approved else "connector" if (conn and role == "part") else role]
        if "colour" in e: o.color = tuple(e["colour"])
        lock(o, role != "part")
        o["kb_id"] = i; o["kb_role"] = role; o["kb_rel"] = rel or "connector: " + e["connector"]["kind"]
        o["kb_parent"] = par or ""; o["kb_on"] = on; o["kb_on_frame"] = G.flat16(frames[par][on]) if par and on != "self" else G.flat16(np.eye(4))
        o["kb_own_in_obj"] = G.flat16(K); o["kb_frames"] = json.dumps({k: G.flat16(v) for k, v in fr.items() if k != "self"})
        o["kb_joint"] = e.get("joint", ""); o["kb_note"] = e.get("note", ""); o["kb_preset"] = bool(e.get("preset"))
        o["kb_from"] = json.dumps(pose)
        objs[i] = o; info[i] = dict(W=W, P=P)
        log.append("%-10s %-9s %s%s" % (i, role, o.name, "  (pre-set)" if e.get("preset") else ""))
    torso = next((objs[e["id"]] for e in spec["objects"] if e["role"] == "host"), None)
    for e in spec["objects"]:
        if e.get("mirror") and torso is not None:
            import mirror; mirror.mirror_live(objs[e["id"]], torso)
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


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        {"build": build, "read": read, "compare": compare}[A[0]](A)
    except SystemExit as e:
        print("STOPPED:", e, flush=True)
    sys.stdout.flush(); os._exit(0)
