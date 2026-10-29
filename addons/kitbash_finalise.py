# Kitbash Finalise - boolean a socketed kitbash into print pieces.
#
# Works on a model built with Part Sockets / TIOW Inbox (parts parented to
# sockets, sockets parented to parts). One button:
#
#   1. checks every part is manifold (the Manifold boolean solver needs it);
#      parts that aren't are listed and can be unioned with Exact instead,
#   2. asks whether the model prints as sub-assemblies and which pieces
#      come off (an arm and everything on it, the head, the pack, ...),
#   3. copies the parts into a "Finalise - <model>" collection (the
#      originals are only hidden) and booleans each piece together in a
#      fixed joint order (torso <- legs, arms, head, pack; arm <- hand,
#      weapon, pauldron, ...) through Hard Ops' own boolean setup, solver
#      Manifold,
#   4. for every piece that comes off: a Part Sockets push-fit peg (spike) on the
#      piece, in the middle of the joint face, and its cavity in the body; the
#      model's ID letter (one per model) as big as fits on the piece's face
#      where it plugs in, and once on the body (the face the legs plug into);
#      and (optionally) the piece's own shape carved out of the body where the
#      two overlap.
#
# Everything stays live (modifiers, cutters on a controller empty per joint)
# so pegs and letters can be moved before Apply Booleans bakes the pieces.

bl_info = {
    "name": "Kitbash Finalise",
    "author": "Josh Parkin-Kelly, Claude",
    "version": (0, 3, 3),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > Finalise",
    "description": "Boolean a socketed kitbash into print pieces with push-fit pegs and ID letters",
    "category": "Object",
}

import math
import re
import sys

import bmesh
import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty,
                       IntProperty, StringProperty)
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SOCK = "ws_type"
TAG = "fa_build"            # on every object a build makes (value = build id)
ROLE = "fa_role"            # host / member / peg / cavity / letter / carve / ctrl
DEFAULT_ORDER = ("Waist, Flat Waist, Shoulder, Neck, Back, Hand, Grip, Shield, Forearm, "
                 "Pad, Shin, Hip, Belt, Back Top, Pack Fin, Wing, Cable, Servo Arm, "
                 "Mechadendrite, Bike, Base")


# ------------------------------------------------------------------ modules

def _module(suffix, attr):
    for name, mod in list(sys.modules.items()):
        if name.endswith(suffix) and hasattr(mod, attr):
            return mod
    return None


def ps_conn():
    return _module("part_sockets.connectors", "bayonet_peg")


def ps_core():
    return _module("part_sockets.core", "surface_aligned_frame")


def hops_bool():
    return _module("hardops.operators.booleans.operator", "add")


def hops_addon():
    return _module("hardops.utility.addon", "preference")


def conn_dims_long(scene, conn):
    """Part Sockets' connector size for the scene's scale and size, always in
    its Long proportions (a proper peg, not the shallow Disc); Custom uses the
    diameter / length sliders."""
    if scene.ws_conn_size == 'CUSTOM':
        return scene.ws_conn_width, scene.ws_conn_length, scene.ws_conn_letter_size
    return conn.CONN_PRESETS[scene.ws_conn_scale]['LONG'][scene.ws_conn_size]


def get_prefs():
    a = bpy.context.preferences.addons.get(__name__)
    return a.preferences if a else None


DEFAULT_NO_PEG = "Waist, Flat Waist"


def no_peg_joints():
    prefs = get_prefs()
    return {x.strip() for x in (prefs.no_peg if prefs else DEFAULT_NO_PEG).split(",") if x.strip()}


# ------------------------------------------------------------------ assembly

def is_socket(o):
    return o is not None and o.get(SOCK) is not None


def is_cutter(o):
    if o.get(ROLE) or o.name.startswith(("WS_", "FA_")):
        return True
    if o.display_type in {'WIRE', 'BOUNDS'}:
        return True
    hops = getattr(o, "hops", None)
    return bool(hops is not None and getattr(hops, "status", "") == "BOOLSHAPE")


def root_of(o):
    while o.parent is not None:
        o = o.parent
    return o


def descendants(o):
    for c in o.children:
        yield c
        yield from descendants(c)


def joint_socket(part):
    """The socket this part is snapped to (Part Sockets' record, else a socket parent)."""
    core = ps_core()
    if core is not None:
        try:
            s = core.snap_socket_of(part)
            if s is not None:
                return s
        except (AttributeError, ReferenceError):
            pass
    return part.parent if is_socket(part.parent) else None


def joint_type(part):
    s = joint_socket(part)
    return str(s.get(SOCK)) if s is not None else ""


def joint_base(t):
    return re.sub(r"\s+[RL]$", "", t)


def parent_part(part, members):
    """Nearest ancestor that is one of the assembly's parts."""
    s = joint_socket(part)
    o = s.parent if s is not None else part.parent
    while o is not None and o not in members:
        o = o.parent
    return o


def assembly(root):
    """Visible mesh parts of the model under root (sockets, cutters and hidden variants left out)."""
    parts = [o for o in [root] + list(descendants(root))
             if o.type == 'MESH' and not is_socket(o) and not is_cutter(o) and o.visible_get()]
    return parts


def order_key(part):
    prefs = get_prefs()
    order = [x.strip() for x in (prefs.joint_order if prefs else DEFAULT_ORDER).split(",") if x.strip()]
    b = joint_base(joint_type(part))
    return order.index(b) if b in order else len(order)


def depth_of(part, members):
    d, p = 0, parent_part(part, members)
    while p is not None:
        d, p = d + 1, parent_part(p, members)
    return d


def tree_order(parts):
    """Parts depth-first from the root, siblings in joint order."""
    members = set(parts)
    kids = {p: [] for p in parts}
    roots = []
    for p in parts:
        pp = parent_part(p, members)
        (kids[pp] if pp is not None else roots).append(p)
    out = []

    def walk(p):
        out.append(p)
        for k in sorted(kids[p], key=lambda k: (order_key(k), k.name)):
            walk(k)
    for r in sorted(roots, key=lambda k: k.name):
        walk(r)
    return out


# ------------------------------------------------------------------ mesh checks

def world_bmesh(ob, deps):
    me = ob.evaluated_get(deps).to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    ob.evaluated_get(deps).to_mesh_clear()
    bm.transform(ob.matrix_world)
    return bm


def manifold_report(ob, deps):
    """'' when the Manifold solver can take this mesh, else what is wrong."""
    me = ob.evaluated_get(deps).to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    ob.evaluated_get(deps).to_mesh_clear()
    try:
        if not bm.faces:
            return "no faces"
        open_e = sum(1 for e in bm.edges if not e.is_manifold)
        flip = sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous)
        bad_v = sum(1 for v in bm.verts if not v.is_manifold)
    finally:
        bm.free()
    bits = []
    if open_e:
        bits.append(f"{open_e} open/non-manifold edges")
    if flip:
        bits.append(f"{flip} flipped edges")
    if bad_v and not open_e:
        bits.append(f"{bad_v} non-manifold verts")
    return ", ".join(bits)


def toolbox_ready():
    """3D Print Toolbox's Make Manifold is available (the extension is enabled)."""
    try:
        return hasattr(bpy.types, "MESH_OT_print3d_clean_non_manifold") or "print3d_clean_non_manifold" in dir(bpy.ops.mesh)
    except Exception:
        return False


def make_manifold(ctx, ob):
    """Run 3D Print Toolbox's Make Manifold on one object (a Finalise copy, never
    your original): loose bits and interior faces removed, doubles merged, holes
    filled, normals made consistent. Returns what is still wrong ('' = fixed)."""
    vl = ctx.view_layer
    active = vl.objects.active
    chosen = [o for o in vl.objects if o.select_get()]
    for o in chosen:
        o.select_set(False)
    ob.hide_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    area = None
    for win in ctx.window_manager.windows:
        for a in win.screen.areas:
            if a.type == 'VIEW_3D':
                area = (win, a)
                break
        if area:
            break
    try:
        kw = {"active_object": ob, "object": ob, "selected_objects": [ob], "selected_editable_objects": [ob]}
        if area:
            kw.update(window=area[0], area=area[1])
        with ctx.temp_override(**kw):
            bpy.ops.mesh.print3d_clean_non_manifold()
    finally:
        if ctx.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        ob.select_set(False)
        for o in chosen:
            if o.name in vl.objects:
                o.select_set(True)
        vl.objects.active = active
    return manifold_report(ob, ctx.evaluated_depsgraph_get())


# ------------------------------------------------------------------ booleans

def _select_only(ctx, objs, active):
    for o in list(ctx.view_layer.objects):
        if o.select_get():
            o.select_set(False)
    for o in objs:
        if o.name in ctx.view_layer.objects:
            o.hide_set(False)
            o.select_set(True)
    active.hide_set(False)
    active.select_set(True)
    ctx.view_layer.objects.active = active


def add_booleans(ctx, host, cutters, operation, solver, use_hops):
    """Boolean cutters into host: Hard Ops' own setup (its boolean modifier,
    Cutters collection, boolshape display, modifier sort) with the solver
    forced, else plain Boolean modifiers set up the same way. The new
    modifiers start switched off in the viewport (a draft: Preview turns a
    piece's on); their names are kept on the host for Preview / Apply.
    Returns how it was done."""
    cutters = [c for c in cutters if c is not None]
    if not cutters:
        return ""
    before = set(m.name for m in host.modifiers)
    how = "Blender Boolean"
    hb, ha = (hops_bool(), hops_addon()) if use_hops else (None, None)
    prop = None
    if hb is not None and ha is not None:
        try:
            prop = ha.preference().property
            old = (prop.boolean_solver, prop.workflow)
        except Exception:
            prop = None
    if prop is not None:
        try:
            prop.boolean_solver = solver
            prop.workflow = 'NONDESTRUCTIVE'        # live until Apply Booleans
            _select_only(ctx, cutters, host)
            hb.add(ctx, operation=operation, collection='Cutters', boolshape=True, sort=True)
            how = "Hard Ops"
        except Exception as exc:                    # a Hard Ops change: carry on without it
            print("[Kitbash Finalise] Hard Ops boolean failed, using Blender's:", repr(exc))
            import traceback; traceback.print_exc()
            for m in [m for m in host.modifiers if m.name not in before]:
                host.modifiers.remove(m)
            prop = None
        finally:
            try:
                prop_restore = ha.preference().property
                prop_restore.boolean_solver, prop_restore.workflow = old
            except Exception:
                pass
        for m in host.modifiers:                    # HOps' node workflow: same solver
            if m.name not in before and hasattr(m, "solver") and m.solver != solver:
                m.solver = solver
    if prop is None:
        for c in cutters:
            m = host.modifiers.new(f"FA {operation.title()} {c.name}"[:63], 'BOOLEAN')
            m.operation = operation
            m.object = c
            m.solver = solver
            m.show_expanded = False
            c.display_type = 'WIRE'
            c.hide_render = True
    names = list(host.get("fa_mods", []))
    for m in host.modifiers:
        if m.name not in before:
            m.show_viewport = False
            names.append(m.name)
    host["fa_mods"] = names
    for c in cutters:
        c["fa_host"] = host.name
    return how


def bake_solid(ctx, name, pieces):
    """One closed mesh from [(mesh, matrix)]: the first with the rest unioned
    into it (Manifold), in the pieces' shared frame."""
    objs = []
    for i, (me, mat) in enumerate(pieces):
        ob = bpy.data.objects.new(f"{name}_tmp{i}", me)
        ctx.scene.collection.objects.link(ob)
        ob.matrix_world = mat
        objs.append(ob)
    base = objs[0]
    for c in objs[1:]:
        m = base.modifiers.new("u", 'BOOLEAN')
        m.operation, m.object, m.solver = 'UNION', c, 'MANIFOLD'
    deps = ctx.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(base.evaluated_get(deps))
    out.transform(pieces[0][1])
    for ob in objs:
        me = ob.data
        bpy.data.objects.remove(ob)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    out.name = name
    return out


# ------------------------------------------------------------------ connectors

def square_peg(name, side, length, taper_deg, embed, grow=0.0, nose=0.35, mouth=0.0, key=0.3):
    """Part Sockets' push-fit peg made square, with one corner cut off (the
    +X +Y corner, by key x side along each edge) so it only goes in one way
    round. Same build as Part Sockets' connector_mesh: spans z = +embed
    (into the owner) to z = -length, tapered, a lead-in nose over the last
    nose x length; grow = clearance all round (the hole); mouth flares the
    hole's entry."""
    h = side / 2.0 + grow
    c = side - key * side + grow * math.sqrt(2.0)          # the cut corner's line: x + y = c
    pts = [(h, -h), (h, c - h), (c - h, h), (-h, h), (-h, -h)]
    shrink = length * math.tan(math.radians(taper_deg))
    s_body = max(0.15, (h - shrink) / h)
    s_tip = max(0.10, s_body * 0.6)
    rings = []
    if mouth > 0.0:
        land = length * (1.0 - nose)
        rings += [(1.0 + mouth, embed), (1.0, -min(0.3, 0.5 * land))]
    else:
        rings.append((1.0, embed))
    rings += [(s_body, -length * (1.0 - nose)), (s_tip, -length)]
    bm = bmesh.new()
    loops = [[bm.verts.new((x * s, y * s, z)) for x, y in pts] for s, z in rings]
    m = len(pts)
    bm.faces.new(loops[0])
    bm.faces.new(list(reversed(loops[-1])))
    for la, lb in zip(loops, loops[1:]):
        for i in range(m):
            bm.faces.new((la[i], la[(i + 1) % m], lb[(i + 1) % m], lb[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


class Ray:
    """World-space geometry of an object's evaluated mesh: BVH for casts and
    nearest-point queries, plus its vertices and vertex normals."""

    def __init__(self, ob, deps):
        import numpy as np
        ev = ob.evaluated_get(deps)
        me = ev.to_mesh()
        n = len(me.vertices)
        co = np.empty(n * 3, np.float64)
        me.vertices.foreach_get("co", co)
        nr = np.empty(n * 3, np.float64)
        me.vertex_normals.foreach_get("vector", nr)
        me.calc_loop_triangles()
        nt = len(me.loop_triangles)
        tv = np.empty(nt * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", tv)
        bm = bmesh.new()
        bm.from_mesh(me)
        ev.to_mesh_clear()
        mw = ob.matrix_world
        bm.transform(mw)
        self.tree = BVHTree.FromBMesh(bm)
        bm.free()
        self.tv = tv.reshape(-1, 3)
        M = np.array(mw)
        N = np.array(mw.to_3x3().inverted_safe().transposed())
        self.co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        nr = nr.reshape(-1, 3) @ N.T
        self.nr = nr / np.maximum(np.linalg.norm(nr, axis=1), 1e-12)[:, None]
        T = self.co[self.tv]
        fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        self.area = np.linalg.norm(fn, axis=1) / 2
        self.fn = fn / np.maximum(2 * self.area, 1e-12)[:, None]
        self.T = T
        self.lo = self.co.min(0) if n else np.zeros(3)
        self.hi = self.co.max(0) if n else np.zeros(3)

    def sample(self, n, mask=None, seed=0):
        """n points spread evenly over the surface (or the masked triangles): (points, normals)."""
        import numpy as np
        w = self.area if mask is None else self.area * mask
        if w.sum() <= 0:
            return np.zeros((0, 3)), np.zeros((0, 3))
        rs = np.random.default_rng(seed)
        idx = rs.choice(len(w), n, p=w / w.sum())
        u, v = rs.random(n), rs.random(n)
        flip = u + v > 1
        u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
        T = self.T[idx]
        P = T[:, 0] + u[:, None] * (T[:, 1] - T[:, 0]) + v[:, None] * (T[:, 2] - T[:, 0])
        return P, self.fn[idx]

    def cast(self, origin, direction, dist):
        loc, nrm, _i, d = self.tree.ray_cast(origin, direction, dist)
        return (loc, nrm, d) if loc is not None else None

    def nearest(self, p):
        loc, nrm, _i, d = self.tree.find_nearest(p)
        return loc, nrm


def frame_from_z(origin, z, xref):
    z = z.normalized()
    x = xref - z * xref.dot(z)
    if x.length < 1e-4:
        ref = Vector((0, 0, 1)) if abs(z.z) < 0.9 else Vector((0, 1, 0))
        x = ref.cross(z)
    x.normalize()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = origin
    return m


def contact(body, piece, tol=0.3, n=30000):
    """Points spread over the body's surface (with its face normals) that lie
    on, or within tol of, the piece's surface: where the two meet."""
    import numpy as np
    lo = piece.co.min(0) - 1.0
    hi = piece.co.max(0) + 1.0
    inside = np.all((body.T.min(1) < hi) & (body.T.max(1) > lo), axis=1)
    pts, nrs = body.sample(n, inside.astype(float))
    keep = np.zeros(len(pts), bool)
    for i, q in enumerate(pts):
        loc, _n, _i, d = piece.tree.find_nearest(Vector(q), tol)
        keep[i] = loc is not None
    return pts[keep], nrs[keep]


def _sphere(n):
    import numpy as np
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = math.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], 1)


def pull_direction(nrs, toward=None):
    """The way the piece comes off: the direction every contact face lets it
    move along (the body's normals at the contact all point at least a little
    that way - a cup's walls sideways, its floor straight along). Scored as
    the mean of n.d less 8 x the mean push into a face (max(0, -n.d)), so
    even a small wall on one side rules out leaning into it; best of a sphere
    of directions, then refined. toward (from where they touch to the
    piece's middle) breaks ties: a foot sunk into a base only touches it round
    its sides, which allow straight up as much as straight down."""
    import numpy as np
    tw = np.array(toward) if toward is not None else np.zeros(3)

    def score(D):
        dots = nrs @ D.T
        return dots.mean(0) - 8.0 * np.maximum(0.0, -dots).mean(0) + 0.05 * (D @ tw)
    D = _sphere(700)
    best = D[int(np.argmax(score(D)))]
    step = 0.12
    for _ in range(4):
        J = best + step * _sphere(60)
        J /= np.linalg.norm(J, axis=1)[:, None]
        J = np.vstack([best, J])
        best = J[int(np.argmax(score(J)))]
        step *= 0.5
    return Vector(best)


def _depth(ray, start, direction, limit=30.0):
    """How far the solid goes from a point on its surface, along direction."""
    h = ray.cast(start + direction * 0.01, direction, limit)
    return h[2] + 0.01 if h is not None else 0.0


class Surf:
    """Several parts cast as one surface (a piece is every part on it)."""

    def __init__(self, rays):
        self.rays = list(rays)

    def near(self, lo, hi):
        import numpy as np
        return Surf([r for r in self.rays if np.all(r.lo <= hi) and np.all(r.hi >= lo)])

    def cast(self, origin, direction, dist):
        best = None
        for r in self.rays:
            loc, nrm, _i, d = r.tree.ray_cast(origin, direction, dist)
            if loc is not None and (best is None or d < best[2]):
                best = (loc, nrm, d)
        return best


def _components(mask, H=None, tol=0.0):
    """4-connected patches of a boolean grid: (labels, sizes); -1 = not in the
    mask. With heights H, neighbours more than tol apart aren't joined (a step)."""
    import numpy as np
    nu, nv = mask.shape
    lab = np.full(nu * nv, -1, np.int64)
    m = mask.ravel()
    h = H.ravel() if H is not None else None
    sizes = []
    for start in np.flatnonzero(m):
        if lab[start] >= 0:
            continue
        k = len(sizes)
        lab[start] = k
        stack, n = [int(start)], 0
        while stack:
            c = stack.pop()
            n += 1
            i, j = divmod(c, nv)
            for d, ok in ((c - nv, i > 0), (c + nv, i < nu - 1), (c - 1, j > 0), (c + 1, j < nv - 1)):
                if ok and m[d] and lab[d] < 0 and (h is None or abs(h[d] - h[c]) <= tol):
                    lab[d] = k
                    stack.append(d)
        sizes.append(n)
    return lab.reshape(nu, nv), sizes


def _fill_holes(C):
    import numpy as np
    lab, sizes = _components(~C)
    if not sizes:
        return C
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    holes = (~C) & ~np.isin(lab, list(edge))
    return C | holes


class JointGrid:
    """The two mating faces of a joint sampled on a grid across it: a plane at
    right angles to the pull-off axis z through the socket, and per cell the
    height (along z) and facing of the piece's face looking down at the body
    (hp, fp) and of the body's face looking up at the piece (hb, fb). Coarse
    first, then fine where the two faces meet."""

    def __init__(self, body, piece, z, xref, origin, cpts, step=0.1, coarse=4):
        import numpy as np
        self.z = Vector(z).normalized()
        fr = frame_from_z(Vector(origin), self.z, xref)
        self.x = Vector(fr.col[0][:3])
        self.y = Vector(fr.col[1][:3])
        self.o = Vector(origin)
        self.step = step
        X, Y, Z, O = (np.array(v) for v in (self.x, self.y, self.z, self.o))
        ulo = vlo = -6.0
        uhi = vhi = 6.0
        zlo, zhi = -5.0, 5.0
        if len(cpts) >= 12:
            rel = np.asarray(cpts) - O
            U, V, H = rel @ X, rel @ Y, rel @ Z
            a, b = max(U.min() - 3.0, -14.0), min(U.max() + 3.0, 14.0)
            c, d = max(V.min() - 3.0, -14.0), min(V.max() + 3.0, 14.0)
            if a < b and c < d:
                ulo, uhi, vlo, vhi = a, b, c, d
                zlo, zhi = H.min() - 4.0, H.max() + 4.0
        self.zlo, self.zhi = zlo, zhi
        corners = np.array([O + X * u + Y * v + Z * h for u in (ulo, uhi) for v in (vlo, vhi) for h in (zlo, zhi)])
        lo, hi = corners.min(0) - 0.5, corners.max(0) + 0.5
        self.body, self.piece = body.near(lo, hi), piece.near(lo, hi)
        self.us = np.arange(ulo, uhi + 1e-9, step)
        self.vs = np.arange(vlo, vhi + 1e-9, step)
        nu, nv = len(self.us), len(self.vs)
        self.hp = np.full((nu, nv), np.nan)
        self.hb = np.full((nu, nv), np.nan)
        self.fp = np.zeros((nu, nv))
        self.fb = np.zeros((nu, nv))
        span = zhi - zlo
        bcast, pcast = self.body.cast, self.piece.cast
        o, x, y, zz = self.o, self.x, self.y, self.z
        mz = -zz
        us, vs, hp, hb, fp, fb = self.us, self.vs, self.hp, self.hb, self.fp, self.fb

        def probe(i, j):
            P = o + x * float(us[i]) + y * float(vs[j])
            a = pcast(P + zz * zlo, zz, span)
            if a is not None:
                hp[i, j] = zlo + a[2]
                fp[i, j] = a[1].dot(zz)
            b = bcast(P + zz * zhi, mz, span)
            if b is not None:
                hb[i, j] = zhi - b[2]
                fb[i, j] = b[1].dot(zz)
        if not self.body.rays or not self.piece.rays:
            return
        for i in range(0, nu, coarse):
            for j in range(0, nv, coarse):
                probe(i, j)
        C = self.footprint()[::coarse, ::coarse]
        D = C.copy()
        D[1:] |= C[:-1]
        D[:-1] |= C[1:]
        E = D.copy()
        E[:, 1:] |= D[:, :-1]
        E[:, :-1] |= D[:, 1:]
        ni, nj = E.shape
        for i in range(nu):
            ci = min(int(round(i / coarse)), ni - 1)
            row = E[ci]
            if not row.any():
                continue
            for j in range(nv):
                if (i % coarse == 0 and j % coarse == 0) or not row[min(int(round(j / coarse)), nj - 1)]:
                    continue
                probe(i, j)

    def footprint(self, lo=-3.0, hi=3.0):
        """Cells where the piece's face looks down at the body's face and the two
        are at most hi apart (or overlap by up to -lo): hidden once assembled."""
        import numpy as np
        with np.errstate(invalid='ignore'):
            g = self.hp - self.hb
            return (self.fp <= -0.3) & (self.fb >= 0.3) & (g >= lo) & (g <= hi)

    def point(self, u, v, h=0.0):
        return self.o + self.x * float(u) + self.y * float(v) + self.z * float(h)

    def main_face(self, side='piece', tol=0.12):
        """The face where the piece plugs in: the biggest smooth patch (no
        steps) of the piece's surface that looks at the body within the hidden
        band (side 'body': of the body's surface looking at the piece - a
        foot's sole on its base). dict(u, v = its middle (holes filled), mask,
        n = plane normal (towards +z), rms = how far from flat, area mm2) or None."""
        import numpy as np
        Hf = self.hp if side == 'piece' else self.hb
        F = self.footprint() & ((self.fp <= -0.5) if side == 'piece' else (self.fb >= 0.5))
        lab, sizes = _components(F, Hf, tol)
        if not sizes:
            return None
        C = lab == int(np.argmax(sizes))
        filled = _fill_holes(C)
        I, J = np.nonzero(filled)
        uc, vc = float(self.us[I].mean()), float(self.vs[J].mean())
        d2 = (self.us[I] - uc) ** 2 + (self.vs[J] - vc) ** 2
        k = int(np.argmin(d2))
        if d2[k] > (2 * self.step) ** 2:            # a crescent: the nearest point on it
            uc, vc = float(self.us[I[k]]), float(self.vs[J[k]])
        I, J = np.nonzero(C)
        Q = np.stack([self.us[I], self.vs[J], Hf[I, J]], 1)
        c0 = Q.mean(0)
        _u, _s, vt = np.linalg.svd(Q - c0, full_matrices=False)
        nl = vt[2] if vt[2][2] >= 0 else -vt[2]
        rms = float(np.sqrt(np.mean(((Q - c0) @ nl) ** 2)))
        n = (self.x * float(nl[0]) + self.y * float(nl[1]) + self.z * float(nl[2])).normalized()
        return dict(u=uc, v=vc, mask=filled, n=n, rms=rms, area=len(I) * self.step ** 2,
                    h=float(c0[2] + ((uc - c0[0]) * -nl[0] + (vc - c0[1]) * -nl[1]) / max(nl[2], 1e-6)))


def solid_depth(surf, start, direction, limit=30.0):
    """How far a ray from a point on (or in) the solid stays inside it, going
    into it: crossings counted, so parts that overlap each other inside a
    piece don't cut it short."""
    inside, pos, gone = 1, Vector(start), 0.0
    for _ in range(60):
        h = surf.cast(pos + direction * 1e-3, direction, limit - gone)
        if h is None:
            return gone
        gone += h[2] + 1e-3
        pos = Vector(h[0])
        inside += -1 if h[1].dot(direction) > 0 else 1
        if inside <= 0 or gone >= limit:
            return gone
    return gone


def joint_place(sock, body1, piece1, body, piece, piece_center, sizes, side='AUTO', carved=False,
                face_side='piece', force=None, through=False):
    """Where a joint's peg goes.
    Axis: the piece's face where it plugs in (the biggest smooth patch of it
    looking at the body): if that face is flat, straight out of it (the way a
    post slides into its socket); if it's curved (a neck ball), the way the
    piece pulls off the body (pull_direction over where the two touch). A
    socket with a stored Part Sockets connector axis ('ws_conn_frame') is used
    as it is.
    Position: the middle of that face.
    Side: the peg on the piece and the cavity in the body - unless side is
    AUTO and the body is too thin there for the cavity while the piece isn't:
    then the peg goes on the body and the cavity in the piece. force =
    'piece' | 'body' fixes the side. face_side 'body' takes the face from
    the body's side instead (a base: the foot's sole, peg on the foot).
    Size: sizes = [dict(r_wall, need)] biggest first; the first one some side
    can take (within 0.6 mm, the peg shortened) wins, else the first one
    anyway (warned). through = the hole may go right through (a base).
    body1 / piece1 = the two parts the joint is between; body / piece = every
    part on each side (Surf). Returns dict(frame, how, gap, depth, grid, uv,
    peg_on 'piece' | 'body', depth_body, depth_piece)."""
    import numpy as np
    core = ps_core()
    sm = sock.matrix_world.normalized() if sock is not None else Matrix.Translation(piece_center)
    xref = Vector((sm[0][0], sm[1][0], sm[2][0]))
    sp = Vector(sm.translation)
    pts, nrs = contact(body1, piece1)
    stored = None
    if sock is not None and sock.get("ws_conn_frame") and core is not None:
        stored = sock.matrix_world @ core.mat_from_flat(sock["ws_conn_frame"])
        z = Vector((stored[0][2], stored[1][2], stored[2][2])).normalized()
        how = "stored axis"
    elif len(pts) >= 12:
        tw = piece_center - Vector(pts.mean(0))
        z = pull_direction(nrs, tw.normalized() if tw.length > 1e-6 else None)
        how = "pull-off axis"
    else:
        loc, nrm = body1.nearest(sp)
        z = nrm.normalized() if loc is not None else Vector((0, 0, 1))
        if loc is not None and (piece_center - loc).dot(z) < 0:
            z = -z
        how = "nearest body surface"
    grid = JointGrid(body, piece, z, xref, Vector(stored.translation) if stored is not None else sp, pts)
    uc = vc = 0.0
    if stored is None:
        face = grid.main_face(face_side)
        if face is not None and face["rms"] <= 0.1 and face["area"] >= 3.0 \
                and face["n"].dot(z) >= math.cos(math.radians(40)):
            # flat: straight out of it, regridded square to it
            z = face["n"]
            grid = JointGrid(body, piece, z, xref, grid.point(face["u"], face["v"], face["h"]), pts)
            face = grid.main_face(face_side) or face
            how = "square to the " + ("piece's" if face_side == 'piece' else "body's") + " flat face"
        elif face is not None:
            # curved (a neck ball): the socket sits on the ball with Z through its middle;
            # use it when that's a way the piece can come off, else the pull-off axis
            zs = Vector((sm[0][2], sm[1][2], sm[2][2])).normalized()
            if sock is not None and zs.dot(z) >= math.cos(math.radians(30)) \
                    and piece1.nearest(sp)[0] is not None and (piece1.nearest(sp)[0] - sp).length <= 1.0:
                z = zs
                grid = JointGrid(body, piece, z, xref, sp, pts)
                face = grid.main_face(face_side) or face
                face["u"], face["v"] = 0.0, 0.0
                how = "along the socket (curved face)"
            else:
                how += " (curved face)"
        if face is None:
            how += ", no joint face found (on the socket)"
        else:
            uc, vc = face["u"], face["v"]
            off = (grid.point(uc, vc) - sp).length
            how += f", middle of its {face['area']:.0f} mm2 face ({off:.1f} mm from the socket)"
    P = grid.point(uc, vc)
    span = grid.zhi - grid.zlo
    eb = body.cast(P + z * grid.zhi, -z, span)
    ep = piece.cast(P + z * grid.zlo, z, span)
    hb = grid.zhi - eb[2] if eb is not None else 0.0
    hp = grid.zlo + ep[2] if ep is not None else hb
    if carved and hp < hb:
        hb = hp                      # the body is carved down to the piece's face there
    ob, op = P + z * hb, P + z * hp
    x0 = Vector(frame_from_z(Vector(), z, xref).col[0][:3])
    y0 = z.cross(x0)

    def deep(s, o, d, rad):
        """Depth of s into itself along d at o, and round the hole's walls
        (a wall point off the face means the hole would break out past its edge)."""
        rim = []
        for t in np.linspace(0, 2 * math.pi, 8, endpoint=False):
            v = (x0 * math.cos(t) + y0 * math.sin(t)) * rad
            h = s.cast(o + v - d * 1.5, d, 3.0)
            rim.append(solid_depth(s, Vector(h[0]), d) if h is not None and h[1].dot(d) < 0 else 0.0)
        return min(solid_depth(s, o, d), sorted(rim)[1])
    first = pick = None
    for k, sz in enumerate(sizes):
        db, dp = deep(body, ob, -z, sz["r_wall"]), deep(piece, op, z, sz["r_wall"])
        ok_b, ok_p = db >= sz["need"] - 0.6, dp >= sz["need"] - 0.6
        if stored is not None or (force is None and side == 'PIECE'):
            cand = (k, 'piece', ok_b)
        elif force is not None:
            cand = (k, force, through or (ok_p if force == 'body' else ok_b))
        elif ok_b:                       # peg on the piece, hole in the body (the normal way)
            cand = (k, 'piece', True)
        elif ok_p:                       # body too thin there: peg on the body, hole in the piece
            cand = (k, 'body', True)
        else:
            cand = (k, 'body' if dp > db else 'piece', False)
        cand += (db, dp)
        first = first or cand
        if cand[2]:
            pick = cand
            break
    k, peg_on, _good, depth_body, depth_piece = pick or first
    gap = hp - hb
    if stored is not None:
        frame = stored
    elif peg_on == 'piece':
        frame = frame_from_z(ob, z, xref)
    else:
        frame = frame_from_z(op, -z, xref)
    return dict(frame=frame, how=how, gap=max(gap, 0.0), grid=grid, uv=(uc, vc), peg_on=peg_on, size=k,
                depth=depth_body if peg_on == 'piece' else depth_piece,
                depth_body=depth_body, depth_piece=depth_piece)


# ------------------------------------------------------------------ ID letters

def _cheb(G, kmax):
    """Per cell, the biggest k with the (2k+1) x (2k+1) cells around it all in G
    (-1 off G), up to kmax."""
    import numpy as np
    na, nb = G.shape
    idx = np.arange(nb)
    left = np.maximum.accumulate(np.where(~G, idx, -1), axis=1)
    right = np.minimum.accumulate(np.where(~G, idx, nb)[:, ::-1], axis=1)[:, ::-1]
    rd = np.minimum(idx - left, right - idx)        # 0 off G, else half the free run + 1
    d = np.where(G, 0, -1)
    M = rd.copy()
    for k in range(1, kmax + 1):
        if 2 * k + 1 > na:
            break
        up = np.zeros_like(rd)
        up[k:] = rd[:-k]
        dn = np.zeros_like(rd)
        dn[:-k] = rd[k:]
        M = np.minimum(M, np.minimum(up, dn))
        ok = M >= k + 1
        if not ok.any():
            break
        d[ok] = k
    return d


def _letter_axes(t, wsign):
    """The letter's x and y in the grid's (u, v) for a letter turned t, read
    from the +z side (wsign 1) or the -z side (wsign -1)."""
    c, s = math.cos(t), math.sin(t)
    return (c, s), ((-s, c) if wsign > 0 else (s, -c))


def fit_letter(us, vs, step, free, w1, h1, smax, margin, up_uv, wsign):
    """The biggest letter (w1 x h1 per mm of size) that fits inside the free
    cells with margin all round, turned in 15 degree steps, up to smax; among
    near-equal fits the one most upright to up_uv. (size, t, u, v) or None."""
    import numpy as np
    if not free.any():
        return None
    q = step / max(w1, h1)
    cu, cv = q * w1, q * h1
    shrink = 2 * margin / min(w1, h1)
    kmax = int(math.ceil(((smax + shrink) / q - 1) / 2)) + 1
    I, J = np.nonzero(free)
    pu, pv = us[I], vs[J]
    un = math.hypot(*up_uv)
    up = (up_uv[0] / un, up_uv[1] / un) if un > 1e-6 else (0.0, 1.0)
    best = None
    for deg in range(0, 180, 15):
        th = math.radians(deg)
        c, s = math.cos(th), math.sin(th)
        a = pu * c + pv * s
        b = -pu * s + pv * c
        A = np.arange(a.min() - cu, a.max() + 1.5 * cu, cu)
        B = np.arange(b.min() - cv, b.max() + 1.5 * cv, cv)
        AA, BB = np.meshgrid(A, B, indexing='ij')
        U = AA * c - BB * s
        V = AA * s + BB * c
        iu = np.rint((U - us[0]) / step).astype(np.int64)
        iv = np.rint((V - vs[0]) / step).astype(np.int64)
        ok = (iu >= 0) & (iu < len(us)) & (iv >= 0) & (iv < len(vs))
        G = np.zeros(AA.shape, bool)
        G[ok] = free[iu[ok], iv[ok]]
        d = _cheb(G, kmax)
        dm = int(d.max())
        if dm < 0:
            continue
        size = (2 * dm + 1) * q - shrink
        if size <= 0:
            continue
        cells = np.argwhere(d == dm)
        cu_, cv_ = U[cells[:, 0], cells[:, 1]], V[cells[:, 0], cells[:, 1]]
        k = int(np.argmin((cu_ - cu_.mean()) ** 2 + (cv_ - cv_.mean()) ** 2))
        for flip in (0.0, math.pi):
            t = th + flip
            _xl, yl = _letter_axes(t, wsign)
            dev = math.degrees(math.acos(max(-1.0, min(1.0, yl[0] * up[0] + yl[1] * up[1]))))
            score = min(size, smax) - 0.004 * dev
            if best is None or score > best[0]:
                best = (score, min(size, smax), t, float(cu_[k]), float(cv_[k]))
    return best[1:] if best else None


def _interp(us, vs, step, H, qu, qv):
    """Bilinear heights from the grid (cells without a height left out)."""
    import numpy as np
    nu, nv = H.shape
    fu = (np.asarray(qu) - us[0]) / step
    fv = (np.asarray(qv) - vs[0]) / step
    i0 = np.clip(np.floor(fu).astype(np.int64), 0, nu - 2)
    j0 = np.clip(np.floor(fv).astype(np.int64), 0, nv - 2)
    tu = np.clip(fu - i0, 0, 1)
    tv = np.clip(fv - j0, 0, 1)
    num = np.zeros(len(i0))
    den = np.zeros(len(i0))
    for di, dj, w in ((0, 0, (1 - tu) * (1 - tv)), (1, 0, tu * (1 - tv)), (0, 1, (1 - tu) * tv), (1, 1, tu * tv)):
        h = H[i0 + di, j0 + dj]
        good = ~np.isnan(h)
        num += np.where(good, w * np.nan_to_num(h), 0.0)
        den += np.where(good, w, 0.0)
    out = np.where(den > 1e-9, num / np.maximum(den, 1e-9), np.nan)
    if np.isnan(out).any():
        out[np.isnan(out)] = np.nanmean(out) if not np.isnan(out).all() else 0.0
    return out


def unit_letter(ctx, text, half_depth=0.5):
    """The letter at size 1, centred on its outline: (mesh, width, height)."""
    me = letter_mesh(ctx, text, 1.0, half_depth)
    if not len(me.vertices):
        return me, 0.7, 0.7
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    for v in me.vertices:
        v.co.x -= cx
        v.co.y -= cy
    return me, max(xs) - min(xs), max(ys) - min(ys)


def place_letter(grid, side, excl, unit, w1, h1, smax, depth, carve, prefer=None, smin=0.6, margin=0.2):
    """The ID letter on one of a joint's mating faces, as big as the face
    allows: side 'piece' = the piece's face (it looks down -z at the body),
    'body' = the body's face (it looks up +z at the piece; with carve, where
    the piece sinks into the body the letter goes on the carved surface).
    Only where the face is hidden by the other (gap -3 .. 3 mm), faces it
    (within 45 degrees), has no steps, keeps clear of the pegs / cavities in
    excl [(point, axis, radius, from, to along the axis)] and is thick enough behind; inside the
    prefer mask (the face it plugs in by) if it fits there at least 0.8 mm.
    The letter is draped over the face, so a gently curved face works too.
    Returns (mesh, matrix_world, size, in the prefer mask) or None."""
    import numpy as np
    g = grid
    if not g.body.rays or not g.piece.rays:
        return None
    with np.errstate(invalid='ignore'):
        gap = g.hp - g.hb
        hidden = (gap >= -3.0) & (gap <= 3.0)
        if side == 'piece':
            H, face, wsign, thick = g.hp.copy(), -g.fp, -1, g.piece
        else:
            H, face, wsign, thick = g.hb.copy(), g.fb.copy(), 1, g.body
            if carve:
                sunk = g.hp < g.hb - 0.02
                H[sunk] = g.hp[sunk]
                face[sunk] = -g.fp[sunk]
        ok = hidden & (face >= 0.7) & ~np.isnan(H)
        Hs = np.where(ok, H, np.nan)                 # the face, for draping
        for ax in (0, 1):
            st = np.abs(np.diff(H, axis=ax)) > 0.15
            if ax == 0:
                ok[1:] &= ~st
                ok[:-1] &= ~st
            else:
                ok[:, 1:] &= ~st
                ok[:, :-1] &= ~st
    if ok.sum() < 9:
        return None
    X, Y, Z, O = (np.array(v) for v in (g.x, g.y, g.z, g.o))
    UU, VV = np.meshgrid(g.us, g.vs, indexing='ij')
    P = O + UU[..., None] * X + VV[..., None] * Y + np.nan_to_num(H)[..., None] * Z
    for a, d, rad, lo, hi in excl:
        rel = P - np.array(a)
        dn = np.array(d) / max(np.linalg.norm(d), 1e-9)
        along = rel @ dn
        perp = rel - along[..., None] * dn
        ok &= (np.linalg.norm(perp, axis=-1) >= rad) | (along < lo) | (along > hi)
    w = g.z * wsign
    wn = np.array(w)
    upw = Vector((0, 0, 1)) if abs(w.z) < 0.7 else Vector((0, -1, 0))   # sideways faces: up; flat ones: the front
    upw = upw - w * upw.dot(w)
    up_uv = (upw.dot(g.x), upw.dot(g.y))
    def attempt(free, floor):
        free = free.copy()
        for _try in range(4):
            fit = fit_letter(g.us, g.vs, g.step, free, w1, h1, smax, margin, up_uv, wsign)
            if fit is None or fit[0] < floor:
                return None
            size, t, uc, vc = fit
            (xa, xb), (ya, yb) = _letter_axes(t, wsign)
            la = (UU - uc) * xa + (VV - vc) * xb
            lb = (UU - uc) * ya + (VV - vc) * yb
            box = free & (np.abs(la) <= size * w1 / 2 + margin) & (np.abs(lb) <= size * h1 / 2 + margin)
            thin = []
            for i, j in np.argwhere(box)[::2]:
                h = thick.cast(Vector(P[i, j]) - w * 0.01, -w, depth + 0.5)
                if h is not None and h[2] + 0.01 < depth + 0.4:
                    thin.append((i, j))
            if not thin:
                return fit
            for i, j in thin:
                free[max(0, i - 1):i + 2, max(0, j - 1):j + 2] = False
        return None
    fit = attempt(ok & prefer, 0.8) if prefer is not None else None
    on_face = fit is not None
    if fit is None:
        fit = attempt(ok, smin)
    if fit is None:
        return None
    size, t, uc, vc = fit
    (xa, xb), (ya, yb) = _letter_axes(t, wsign)
    # drape the unit letter over the face
    n = len(unit.vertices)
    co = np.empty(n * 3)
    unit.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    qu = uc + co[:, 0] * size * xa + co[:, 1] * size * ya
    qv = vc + co[:, 0] * size * xb + co[:, 1] * size * yb
    hv = _interp(g.us, g.vs, g.step, Hs, qu, qv)
    hc = float(_interp(g.us, g.vs, g.step, Hs, [uc], [vc])[0])
    world = O + qu[:, None] * X + qv[:, None] * Y + hv[:, None] * Z \
        + np.where(co[:, 2:3] > 0, 0.25, -depth) * wn
    xl = g.x * xa + g.y * xb
    yl = w.cross(xl)
    M = Matrix((xl, yl, w)).transposed().to_4x4()
    M.translation = g.point(uc, vc, hc)
    R = np.array([np.array(xl), np.array(yl), wn])
    loc = (world - np.array(M.translation)) @ R.T
    me = unit.copy()
    me.vertices.foreach_set("co", loc.ravel())
    me.update()
    return me, M, size, on_face


def letter_mesh(ctx, text, size, half_depth):
    cu = bpy.data.curves.new("FA_letter", 'FONT')
    cu.body = text
    cu.size = size
    cu.extrude = half_depth
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    tmp = bpy.data.objects.new("FA_letter_tmp", cu)
    ctx.scene.collection.objects.link(tmp)
    deps = ctx.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(deps))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.name = f"FA_letter_{text}"
    return me


# ------------------------------------------------------------------ the build

LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"     # no I or O (they read as 1 and 0)


def next_ident():
    """The first letter no other finalised model in the file uses."""
    used = {c.get("fa_letter") for c in bpy.data.collections if c.get(TAG)}
    return next((ch for ch in LETTERS if ch not in used), "A")


def build(ctx, root, parts, splits, exact, opts, log):
    """Copies, pieces, joints and booleans. Everything that reads geometry
    (rays, faces, letters) runs before the first boolean is added, so nothing
    is evaluated through a boolean stack while building."""
    scene = ctx.scene
    vl = ctx.view_layer
    deps = ctx.evaluated_depsgraph_get()
    members = set(parts)
    bid = f"{root.name}"[:40]
    col = bpy.data.collections.new(f"Finalise - {root.name}"[:63])
    scene.collection.children.link(col)
    col[TAG] = bid

    def link(ob, role):
        col.objects.link(ob)
        ob[TAG] = bid
        ob[ROLE] = role
        return ob

    def piece_root(p):
        while p not in splits:
            q = parent_part(p, members)
            if q is None:
                return p
            p = q
        return p

    order = tree_order(parts)
    pieces = {}
    for p in order:
        pieces.setdefault(piece_root(p), []).append(p)
    main = piece_root(order[0])

    # ---- A. read the originals (no booleans exist yet)
    conn = ps_conn()
    joints = [p for p in order if p in splits and parent_part(p, members) is not None]
    if joints and conn is None:
        log.append("Part Sockets is not enabled: no pegs or letters")
        joints = []
    dia = 2.0
    if joints:
        dia, L, _ls = conn_dims_long(scene, conn)
        profile = scene.fa_peg_profile
        ov = scene.ws_conn_oval if profile == 'BAYONET' else 1.0
        cl = scene.ws_conn_clearance
        gap_b = scene.ws_conn_bottom_gap
        taper = scene.ws_conn_taper

        def dims(d, ln, name):
            """r_wall: the hole's walls (its depth is checked out there); r_out: its flared
            mouth (letters keep clear of it); r_peg: the peg where it leaves its face."""
            r_ = d / 2.0
            if profile == 'BAYONET':
                w, o, pg = r_ * ov + cl, r_ * ov + cl, r_ * ov + 0.3
            elif profile == 'SQUARE':                   # out to the corners
                w = (r_ + cl) * math.sqrt(2.0)
                o, pg = w * 1.18, r_ * math.sqrt(2.0)
            else:
                w, o, pg = r_ + cl, (r_ + cl) * 1.18, r_
            return dict(dia=d, L=ln, r=r_, r_wall=w, r_out=o, r_peg=pg, need=ln + gap_b + 0.3, name=name)
        # the chosen size first, then the smaller Part Sockets sizes for joints it won't fit
        sizes = [dims(dia, L, scene.ws_conn_size)]
        if scene.ws_conn_size != 'CUSTOM':
            for nm, (d2, l2, _x) in sorted(conn.CONN_PRESETS[scene.ws_conn_scale]['LONG'].items(),
                                           key=lambda kv: -kv[1][0]):
                if d2 < dia:
                    sizes.append(dims(d2, l2, nm))
    nopeg = opts.get("nopeg", set())
    ident = (opts.get("ident") or "A").strip().upper()[:3] or "A"
    ldepth, lmax = opts["letter_depth"], opts["letter_size"]
    rays = {}

    def ray(o):
        if o not in rays:
            rays[o] = Ray(o, deps)
        return rays[o]

    def surf(objs):
        return Surf([ray(m) for m in objs])

    plans = []
    for i, s in enumerate(joints):
        p = parent_part(s, members)
        tag = str(i + 1)
        sock = joint_socket(s)
        pc = s.matrix_world @ (sum((Vector(v) for v in s.bound_box), Vector()) / 8.0)
        body_root = piece_root(p)
        carve = []
        if opts["carve"]:
            # the piece's parts that really overlap the body they come off
            for m in pieces[s]:
                if any(ray(m).tree.overlap(ray(bp).tree) for bp in pieces[body_root]):
                    carve.append(m)
        base = joint_base(joint_type(s)) == "Base"
        # a base: the peg on the foot (the body side), in the middle of the sole that stands on it
        jf = joint_place(sock, ray(p), ray(s), surf(pieces[body_root]), surf(pieces[s]), pc,
                         sizes if s not in nopeg else sizes[:1],
                         side=opts.get("peg_side", 'AUTO'), carved=bool(carve),
                         face_side='body' if base else 'piece', force='body' if base else None, through=base)
        frame, gap, depth, peg_on = jf["frame"], jf["gap"], jf["depth"], jf["peg_on"]
        sz = sizes[jf["size"]]
        Lj, need, dj, rj = sz["L"], sz["need"], sz["dia"], sz["r"]
        warn = []
        if jf["size"] > 0:
            warn.append(f"size {sz['name']} ({dj:.1f} mm): {sizes[0]['name']} doesn't fit either side here")
        hole = "body" if peg_on == 'piece' else "piece"
        if s in nopeg:
            plans.append(dict(s=s, p=p, tag=tag, frame=frame, aim="no peg (as set)", gap=gap, warn=[], L=0.0,
                              peg_on=peg_on, grid=jf["grid"], body_root=body_root, carve=carve, peg=None, cavity=None,
                              sz=sz))
            continue
        if base:
            warn.append("peg on the foot, hole in the base" + (
                f" (the hole goes through: base {depth:.1f} mm there)" if depth < need else ""))
        elif peg_on == 'body':
            warn.append(f"peg on the body, hole in the piece: the body is only {jf['depth_body']:.1f} mm "
                        f"deep in the middle of the face (the cavity needs {need:.1f})")
        if depth < need and not base:
            Lj = round(depth - gap_b - 0.3, 2)
            if Lj < 1.0:
                Lj = 1.0
                warn.append(f"{hole} only {depth:.1f} mm deep at the peg: the cavity would break through, "
                            f"move the arrow or use a smaller size")
            else:
                warn.append(f"peg shortened to {Lj:.2f} mm ({hole} {depth:.1f} mm deep there)")
        if gap > 0.5:
            warn.append(f"peg bridges a {gap:.1f} mm gap")
        if profile == 'BAYONET':
            peg_me = bake_solid(ctx, f"FA_peg_{tag}", conn.bayonet_peg(tag, rj, Lj, ov, shank_top=max(0.4, gap + 0.4)))
            cav_me = bake_solid(ctx, f"FA_cavity_{tag}", conn.bayonet_cavity(tag, rj, Lj, ov, cl, gap_b))
        elif profile == 'SQUARE':
            # square, one corner cut: it only goes in one way round, as posed (turns with the socket's X)
            peg_me = square_peg(f"FA_peg_{tag}", dj, Lj, taper, embed=max(0.4, gap + 0.4))
            cav_me = square_peg(f"FA_cavity_{tag}", dj, Lj + gap_b, taper, embed=0.6, grow=cl, mouth=0.18)
        else:
            # Part Sockets' push-fit peg: a tapered spike with a lead-in nose, into a clearance
            # cavity with a flared mouth (QUAD adds four flats so it only seats every 90 degrees)
            flats = 4 if profile == 'QUAD' else 0
            peg_me = conn.connector_mesh(f"FA_peg_{tag}", rj, Lj, taper, embed=max(0.4, gap + 0.4), flats=flats)
            cav_me = conn.connector_mesh(f"FA_cavity_{tag}", rj, Lj + gap_b, taper, embed=0.6, grow=cl,
                                         flats=flats, mouth=0.18)
        plans.append(dict(s=s, p=p, tag=tag, frame=frame, aim=jf["how"], gap=gap, warn=warn, L=Lj, peg_on=peg_on,
                          grid=jf["grid"], body_root=body_root, carve=carve, peg=peg_me, cavity=cav_me, sz=sz))

    # one letter per model: on every piece's face where it plugs in, and once on the main body
    letters = []                       # (piece root, mesh, matrix, plan to follow or None, note)
    if opts["letters"] and plans:
        unit, w1, h1 = unit_letter(ctx, ident)

        def axis(pl):
            f = pl["frame"]
            return Vector(f.translation), Vector((f[0][2], f[1][2], f[2][2]))

        def excl(pr):
            out = []
            for pl in plans:
                if pl["peg"] is None:
                    continue
                a, d = axis(pl)
                owner, other = (pl["s"], pl["body_root"]) if pl["peg_on"] == 'piece' else (pl["body_root"], pl["s"])
                lo, hi = -(pl["L"] + gap_b + 1.0), pl["gap"] + 1.5      # just along the peg and its hole
                if owner is pr:
                    out.append((a, d, pl["sz"]["r_peg"] + 0.25, lo, hi))
                if other is pr:
                    out.append((a, d, pl["sz"]["r_out"] + 0.25, lo, hi))
            return out

        def tip_letter(pl, pr):
            """No room on the face: on the peg's tip / the cavity's floor (moves with the peg)."""
            f = pl["frame"]
            r, dia = pl["sz"]["r"], pl["sz"]["dia"]
            if (pl["peg_on"] == 'piece') == (pr is pl["s"]):
                if profile == 'BAYONET':
                    m = f @ Matrix.Translation((0, -r * 0.55 * 0.5, -pl["L"])) @ Matrix.Rotation(math.pi, 4, 'X')
                    size = min(lmax, r * 0.55 * 0.9)
                elif profile == 'SQUARE':
                    s_body = max(0.15, (r - pl["L"] * math.tan(math.radians(taper))) / r)
                    m = f @ Matrix.Translation((0, 0, -pl["L"])) @ Matrix.Rotation(math.pi, 4, 'X')
                    size = min(lmax, dia * max(0.10, s_body * 0.6) * 0.75)
                else:   # the tapered tip's flat end (as Part Sockets sizes it)
                    s_body = max(0.15, (r - pl["L"] * math.tan(math.radians(taper))) / r)
                    m = f @ Matrix.Translation((0, 0, -pl["L"])) @ Matrix.Rotation(math.pi, 4, 'X')
                    size = min(lmax, dia * max(0.10, s_body * 0.55) * 0.8)
                note = f"on the peg's tip ({size:.1f} mm), no room on the face"
            else:
                m = f @ Matrix.Translation((0, 0, -(pl["L"] + gap_b)))
                size = min(lmax, r * 0.9)
                note = f"on the floor of joint {pl['tag']}'s hole ({size:.1f} mm), no room on the face"
            letters.append((pr, letter_mesh(ctx, ident, size, ldepth), m, pl, note))

        for pl in plans:
            mf = pl["grid"].main_face()
            res = place_letter(pl["grid"], 'piece', excl(pl["s"]), unit, w1, h1, lmax, ldepth, carve=False,
                               prefer=mf["mask"] if mf else None)
            if res is None and pl["peg"] is None:
                log.append(f"Letter {ident}: no room on {pl['s'].name}'s face")
            elif res is None:
                tip_letter(pl, pl["s"])
            else:
                me, m, size, on_face = res
                letters.append((pl["s"], me, m, None, f"{size:.1f} mm " + (
                    "on its face where it plugs in" if on_face else
                    "on a hidden face beside where it plugs in (no room round the peg)")))
        # the main body: one letter, on the face the legs plug into if there's room, else the biggest
        best = None
        for pl in plans:
            if pl["body_root"] is not main:
                continue
            res = place_letter(pl["grid"], 'body', excl(main), unit, w1, h1, lmax, ldepth, carve=bool(pl["carve"]))
            if res is None:
                continue
            waist = joint_base(joint_type(pl["s"])) in {"Waist", "Flat Waist"}
            key = (waist and res[2] >= 1.5, res[2])
            if best is None or key > best[0]:
                if best is not None:
                    bpy.data.meshes.remove(best[1][0])
                best = (key, res, pl)
            else:
                bpy.data.meshes.remove(res[0])
        if best is not None:
            (_k, (me, m, size, _f), pl) = best
            letters.append((main, me, m, None, f"{size:.1f} mm on the face {pl['s'].name} plugs into"))
        else:
            first = next((pl for pl in plans if pl["body_root"] is main and pl["peg"] is not None), None)
            if first is not None:
                tip_letter(first, main)
            else:
                log.append(f"Letter {ident}: no room on the body")
        bpy.data.meshes.remove(unit)
    rays.clear()

    # ---- B. copies of the parts as they look (modifiers applied), originals hidden
    copies = {}
    for p in order:
        me = bpy.data.meshes.new_from_object(p.evaluated_get(deps))
        c = link(bpy.data.objects.new(f"{p.name} [F]"[:63], me), "member")
        c.matrix_world = p.matrix_world.copy()
        c["fa_src"] = p.name
        copies[p] = c
    if opts.get("make_manifold") and exact:
        for p in [q for q in order if q in exact]:
            try:
                left = make_manifold(ctx, copies[p])
            except Exception as exc:          # a failed clean-up leaves the copy as it was
                left = f"Make Manifold failed ({exc})"
            if not left:
                exact.discard(p)
                log.append(f"{p.name}: made manifold (3D Print Toolbox) - Manifold solver")
            else:
                log.append(f"{p.name}: still not manifold after Make Manifold ({left}) - Exact for it")
    hidden = []
    for o in [root] + list(descendants(root)):
        if o.name in vl.objects and o.visible_get() and not o.get(TAG):
            o.hide_set(True)
            hidden.append(o.name)
    col["fa_hidden"] = hidden

    # ---- C. what each piece gets, in order
    ops = {pr: [] for pr in pieces}          # piece root -> [(op, [objects], needs_exact)]
    bad = lambda *objs: any(o in exact for o in objs)
    for pr, ps in pieces.items():
        copies[pr][ROLE] = "host"
        copies[pr]["fa_kind"] = "body" if pr is main else "piece"
        rest = sorted((q for q in ps if q is not pr), key=lambda q: (order_key(q), depth_of(q, members), q.name))
        for q in rest:
            ops[pr].append(('UNION', [copies[q]], bad(q, pr)))
    ctrls = {}
    for pl in plans:
        s, p, tag, frame = pl["s"], pl["p"], pl["tag"], pl["frame"]
        body_root = pl["body_root"]
        body_host, piece_host = copies[body_root], copies[s]
        for m in pl["carve"]:
            cv = link(bpy.data.objects.new(f"FA_carve_{tag}_{m.name}"[:63], copies[m].data.copy()), "carve")
            cv.matrix_world = m.matrix_world.copy()
            ops[body_root].append(('DIFFERENCE', [cv], bad(m, body_root)))
        if pl["peg"] is None:
            log.append(f"Joint {tag}: {s.name} off {p.name} ({joint_type(s)}): no peg (as set), "
                       f"carve {len(pl['carve'])}")
            continue
        ctrl = link(bpy.data.objects.new(f"FA_joint_{tag}_{s.name}"[:63], None), "ctrl")
        ctrl.empty_display_type = 'ARROWS'
        ctrl.empty_display_size = max(dia * 1.5, 2.0)
        ctrl.parent = body_host
        ctrl.matrix_parent_inverse = body_host.matrix_world.inverted_safe()
        ctrl.matrix_world = frame
        ctrl["fa_piece"] = piece_host.name
        ctrl["fa_body"] = body_host.name
        ctrl["fa_peg_on"] = pl["peg_on"]
        ctrl["fa_L"] = pl["L"]
        ctrls[id(pl)] = ctrl

        def stage(me, world, role, parent=ctrl):
            ob = link(bpy.data.objects.new(me.name, me), role)
            ob.parent = parent
            ob.matrix_parent_inverse = parent.matrix_world.inverted_safe()
            ob.matrix_world = world
            ob.display_type = 'WIRE'
            ob.hide_render = True
            return ob

        owner, other = (s, body_root) if pl["peg_on"] == 'piece' else (body_root, s)
        ops[owner].append(('UNION', [stage(pl["peg"], frame, "peg")], bad(owner)))
        ops[other].append(('DIFFERENCE', [stage(pl["cavity"], frame, "cavity")], bad(other)))
        log.append(f"Joint {tag}: {s.name} off {p.name} ({joint_type(s)}): {pl['L']:.1f} mm peg, {pl['aim']}, "
                   f"gap {pl['gap']:.2f}, carve {len(pl['carve'])}" + ("; " + "; ".join(pl["warn"]) if pl["warn"] else ""))
    for pr, me, m, pl, note in letters:
        parent = ctrls[id(pl)] if pl is not None else copies[pr]
        me.name = f"FA_letter_{ident}_{pr.name}"[:63]
        ob = link(bpy.data.objects.new(me.name, me), "letter")
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted_safe()
        ob.matrix_world = m
        ob.display_type = 'WIRE'
        ob.hide_render = True
        ops[pr].append(('DIFFERENCE', [ob], bad(pr)))
        log.append(f"Letter {ident} on {'the body' if pr is main else pr.name}: {note}")
    if letters:
        col["fa_letter"] = ident

    # ---- D. booleans, per piece in this order: its parts, the carves, pegs, holes, letters (a carve
    # after a peg would cut the peg off again: it sits inside the piece's shape); the Manifold ones
    # first within each. From the first one that needs Exact (a non-manifold part) on, the rest of
    # the piece goes Exact too: that keeps the order, and Exact output can be non-manifold, which the
    # Manifold solver can't take.
    rank = {"member": 0, "carve": 1, "peg": 2, "cavity": 3, "letter": 4}
    how = set()
    for pr, lst in ops.items():
        host = copies[pr]
        lst.sort(key=lambda t: (rank.get(t[1][0].get(ROLE), 0), t[2]))
        exact_from = next((i for i, t in enumerate(lst) if t[2]), len(lst))
        run = []                                       # batch consecutive same-op, same-solver cutters
        for i, (op, objs, _ex) in enumerate(lst):
            ex = i >= exact_from
            if run and run[-1][0] == op and run[-1][2] == ex:
                run[-1][1].extend(objs)
            else:
                run.append((op, list(objs), ex))
        n_exact = 0
        for op, objs, ex in run:
            h = add_booleans(ctx, host, objs, op, 'EXACT' if ex else 'MANIFOLD', opts["use_hops"])
            if h:
                how.add(h)
            if ex:
                n_exact += len(objs)
        log.append(f"{host.name}: {len(lst)} boolean(s)" +
                   (f", {n_exact} with Exact (from the first non-manifold part on)" if n_exact else ""))

    # draft: parts shown as solids, pegs / cavities / letters as wires, booleans off
    for pr, ps in pieces.items():
        for q in ps:
            copies[q]["fa_host"] = copies[pr].name
    for o in bpy.data.objects:
        if o.get(TAG) != bid or o.name not in vl.objects:
            continue
        role = o.get(ROLE)
        if role in {"host", "member"}:
            o.display_type = 'TEXTURED'
            o.hide_set(False)
        elif role in {"peg", "cavity", "letter"}:
            o.display_type = 'WIRE'
            o.hide_set(False)
        elif role == "ctrl":
            o.hide_set(False)
        else:
            o.hide_set(True)
    _select_only(ctx, [], copies[order[0]])
    col["fa_pieces"] = [copies[pr].name for pr in pieces]
    return col, how


# ------------------------------------------------------------------ operators

class FA_Item(bpy.types.PropertyGroup):
    part: StringProperty()
    label: StringProperty()
    depth: IntProperty()
    split: BoolProperty(name="Separate", default=False)
    peg: BoolProperty(name="Peg", default=True, description="A peg and hole where this piece plugs in "
                      "(off: it just sits on its face, still lettered)")


class FA_Bad(bpy.types.PropertyGroup):
    part: StringProperty()
    info: StringProperty()


def current_build(ctx):
    ob = ctx.active_object
    if ob is None:
        return None
    tag = ob.get(TAG)
    if tag is None:
        r = root_of(ob)
        for col in bpy.data.collections:
            if col.get(TAG) == r.name[:40]:
                return col
        return None
    for col in bpy.data.collections:
        if col.get(TAG) == tag:
            return col
    return None


class FA_OT_finalise(bpy.types.Operator):
    """Boolean the selected model into print pieces: check manifold, choose
sub-assemblies, union in joint order (Hard Ops booleans, Manifold solver),
push-fit pegs and ID letters where pieces come off. The originals are kept
(hidden); nothing is applied until Apply Booleans"""
    bl_idname = "fa.finalise"
    bl_label = "Finalise Model"
    bl_options = {'REGISTER', 'UNDO'}

    subassemblies: BoolProperty(name="Print as sub-assemblies", default=False,
                                description="Some pieces print separately and plug in with pegs")
    use_exact: BoolProperty(name="Use Exact for the parts above", default=False,
                            description="Boolean the non-manifold parts (and their pieces) with the Exact solver - slower")
    make_manifold: BoolProperty(name="Make them manifold first (3D Print Toolbox)", default=True,
                                description="Run 3D Print Toolbox's Make Manifold on Finalise's copies of these parts "
                                            "(your originals aren't touched); any still not manifold use Exact")
    carve: BoolProperty(name="Carve overlaps", default=True,
                        description="Cut each separate piece's shape out of the body where they overlap, so it seats back in")
    letters: BoolProperty(name="ID letter", default=True,
                          description="Deboss the model's letter into every piece's face where it plugs in, "
                                      "and once into the body - all hidden once assembled")
    ident: StringProperty(name="Letter", default="A", maxlen=3,
                          description="The model's ID letter: the same on every piece of this model, "
                                      "so a squad's pieces don't get mixed up")

    @classmethod
    def poll(cls, ctx):
        return ctx.mode == 'OBJECT' and ctx.active_object is not None and \
            not ctx.active_object.get(TAG)

    def _scan(self, ctx):
        wm = ctx.window_manager
        root = root_of(ctx.active_object)
        parts = assembly(root)
        wm.fa_items.clear()
        wm.fa_bad.clear()
        members = set(parts)
        deps = ctx.evaluated_depsgraph_get()
        for p in tree_order(parts):
            bad = manifold_report(p, deps)
            if bad:
                it = wm.fa_bad.add()
                it.part, it.info = p.name, bad
            if parent_part(p, members) is None:
                continue
            it = wm.fa_items.add()
            it.part = p.name
            it.depth = depth_of(p, members)
            jb = joint_base(joint_type(p))
            it.peg = jb not in no_peg_joints()
            it.split = jb == "Base"                 # bases print apart: the foot gets a peg into it
            it.label = f"{p.name}  ({joint_type(p) or 'no socket'})"
        wm.fa_root = root.name
        return root, parts

    def invoke(self, ctx, event):
        self.ident = next_ident()
        root, parts = self._scan(ctx)
        if len(parts) < 2:
            self.report({'ERROR'}, f"'{root.name}' has no parts snapped to it")
            return {'CANCELLED'}
        return ctx.window_manager.invoke_props_dialog(self, width=460, title=f"Finalise {root.name}")

    def draw(self, ctx):
        wm = ctx.window_manager
        lay = self.layout
        lay.label(text=f"{len(wm.fa_items) + 1} parts", icon='MESH_DATA')
        if len(wm.fa_bad):
            box = lay.box()
            box.alert = True
            box.label(text="Not manifold - the Manifold solver can't use these:", icon='ERROR')
            for b in wm.fa_bad:
                box.label(text=f"   {b.part}: {b.info}")
            row = box.row()
            row.enabled = toolbox_ready()
            row.prop(self, "make_manifold")
            if not toolbox_ready():
                box.label(text="Enable the 3D Print Toolbox extension to fix them here", icon='INFO')
            box.prop(self, "use_exact")
            if not self.use_exact and not (self.make_manifold and toolbox_ready()):
                box.label(text="Fix them (e.g. 3D Print Toolbox) or tick one of the above to carry on")
        lay.prop(self, "subassemblies")
        if self.subassemblies:
            box = lay.box()
            box.label(text="Pieces printed separately (each takes what's on it):")
            col = box.column(align=True)
            for it in wm.fa_items:
                row = col.row(align=True)
                row.separator(factor=1.5 * max(0, it.depth - 1))
                row.prop(it, "split", text=it.label)
                sub = row.row(align=True)
                sub.enabled = it.split
                sub.prop(it, "peg", toggle=True)
            row = lay.row()
            row.prop(self, "carve")
            row.prop(self, "letters")
            sub = row.row()
            sub.enabled = self.letters
            sub.prop(self, "ident")

    def execute(self, ctx):
        wm = ctx.window_manager
        root = bpy.data.objects.get(wm.fa_root) or root_of(ctx.active_object)
        if not len(wm.fa_items) and not len(wm.fa_bad):
            root, _ = self._scan(ctx)
        parts = assembly(root)
        byname = {p.name: p for p in parts}
        bad = [byname[b.part] for b in wm.fa_bad if b.part in byname]
        fixing = bool(bad) and self.make_manifold and toolbox_ready()
        if bad and not self.use_exact and not fixing:
            self.report({'ERROR'}, "Not manifold: " + ", ".join(p.name for p in bad)
                        + " - fix them, or tick 'Make them manifold first' or 'Use Exact'")
            return {'CANCELLED'}
        splits = set()
        if self.subassemblies:
            splits = {byname[i.part] for i in wm.fa_items if i.split and i.part in byname}
        nopeg = {byname[i.part] for i in wm.fa_items if i.split and not i.peg and i.part in byname}
        prefs = get_prefs()
        opts = dict(use_hops=prefs.use_hops if prefs else True, carve=self.carve and bool(splits),
                    peg_side=ctx.scene.fa_peg_side, nopeg=nopeg,
                    letters=self.letters, ident=self.ident, letter_size=ctx.scene.fa_letter_size,
                    letter_depth=ctx.scene.fa_letter_depth, make_manifold=fixing)
        log = []
        try:
            col, how = build(ctx, root, parts, splits, set(bad), opts, log)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            discard_build(ctx, root.name[:40])
            self.report({'ERROR'}, f"Finalise failed (nothing changed): {exc}")
            return {'CANCELLED'}
        for line in log:
            print("[Kitbash Finalise]", line)
        ctx.scene.fa_last_log = "\n".join(log)
        self.report({'INFO'}, f"{len(col['fa_pieces'])} piece(s) drafted with "
                              f"{' + '.join(sorted(how)) or 'no'} booleans - move the joint arrows if "
                              f"needed, Preview to see a piece, then Apply Booleans")
        return {'FINISHED'}


def build_objects(bid):
    return [o for o in bpy.data.objects if o.get(TAG) == bid]


def set_preview(ctx, host, on):
    """Booleans of one piece on (its parts' copies hidden) or off (draft)."""
    names = set(host.get("fa_mods", []))
    for m in host.modifiers:
        if m.name in names:
            m.show_viewport = on
    for o in build_objects(host[TAG]):
        if o.get("fa_host") == host.name and o is not host and o.get(ROLE) == "member" \
                and o.name in ctx.view_layer.objects:
            o.hide_set(on)
    host["fa_preview"] = on


class FA_OT_preview(bpy.types.Operator):
    """Turn the booleans of the selected finalised pieces on to see the result
(or off again). Pieces with many booleans take a few seconds to show"""
    bl_idname = "fa.preview"
    bl_label = "Preview Booleans"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, ctx):
        return ctx.mode == 'OBJECT' and current_build(ctx) is not None

    def execute(self, ctx):
        col = current_build(ctx)
        hosts = [o for o in build_objects(col[TAG]) if o.get(ROLE) == "host"]
        sel = {o.get("fa_host", o.name) for o in ctx.selected_objects if o.get(TAG) == col[TAG]}
        chosen = [h for h in hosts if h.name in sel] or hosts
        on = not all(h.get("fa_preview") for h in chosen)
        for h in chosen:
            set_preview(ctx, h, on)
        self.report({'INFO'}, f"Booleans {'on' if on else 'off'}: {', '.join(h.name for h in chosen)}")
        return {'FINISHED'}


class FA_OT_apply(bpy.types.Operator):
    """Bake the finalised pieces: apply every boolean (one at a time), delete
the cutters and part copies, and check each piece is manifold"""
    bl_idname = "fa.apply"
    bl_label = "Apply Booleans"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, ctx):
        return ctx.mode == 'OBJECT' and current_build(ctx) is not None

    def execute(self, ctx):
        col = current_build(ctx)
        bid = col[TAG]
        vl = ctx.view_layer
        hosts = [o for o in build_objects(bid) if o.get(ROLE) == "host"]
        ident = col.get("fa_letter")
        report, failed = [], []
        for h in hosts:
            h.hide_set(False)
            for m in list(h.modifiers):
                m.show_viewport = True
                name = m.name
                try:
                    with ctx.temp_override(object=h, active_object=h, selected_objects=[h],
                                           selected_editable_objects=[h]):
                        bpy.ops.object.modifier_apply(modifier=name)
                except RuntimeError as exc:
                    failed.append(f"{h.name}: {name} ({exc})")
                    if name in h.modifiers:
                        h.modifiers.remove(h.modifiers[name])
            h.pop("fa_mods", None)
            h.pop("fa_preview", None)
            what = "Body" if h.get("fa_kind") == "body" else h.get("fa_src", h.name)
            h.name = (f"{bid} - {what}" + (f" [{ident}]" if ident else ""))[:63]
            bad = manifold_report(h, ctx.evaluated_depsgraph_get())
            report.append(f"{h.name}: {'manifold' if not bad else bad}")
        for o in [o for o in build_objects(bid) if o.get(ROLE) != "host"]:
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if isinstance(data, bpy.types.Mesh) and data.users == 0:
                bpy.data.meshes.remove(data)
        for h in hosts:
            h[ROLE] = "piece"
            h.display_type = 'TEXTURED'
            if h.name not in col.objects:
                for c in list(h.users_collection):
                    c.objects.unlink(h)
                col.objects.link(h)
        drop_empty_cutters()
        report += [f"FAILED {f}" for f in failed]
        for line in report:
            print("[Kitbash Finalise]", line)
        ctx.scene.fa_last_log = "\n".join(report)
        bad = [r for r in report if not r.endswith("manifold")]
        self.report({'WARNING'} if bad else {'INFO'},
                    f"{len(hosts)} piece(s) baked" + (f"; problems: {len(bad)} (see panel)" if bad else ", all manifold"))
        return {'FINISHED'}


def drop_empty_cutters():
    """Hard Ops' Cutters collection, once the build's cutters were all that was in it."""
    c = bpy.data.collections.get("Cutters")
    if c is not None and not len(c.objects) and not len(c.children):
        bpy.data.collections.remove(c)


def discard_build(ctx, bid):
    """Remove everything a build made and show the originals it hid."""
    col = next((c for c in bpy.data.collections if c.get(TAG) == bid), None)
    hidden = list(col.get("fa_hidden", [])) if col is not None else []
    for o in [o for o in bpy.data.objects if o.get(TAG) == bid]:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    if col is not None:
        bpy.data.collections.remove(col)
    for n in hidden:
        o = bpy.data.objects.get(n)
        if o is not None and o.name in ctx.view_layer.objects:
            o.hide_set(False)
    drop_empty_cutters()


class FA_OT_discard(bpy.types.Operator):
    """Delete the finalise draft (or baked pieces) and show the original parts again"""
    bl_idname = "fa.discard"
    bl_label = "Discard Finalise"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, ctx):
        return ctx.mode == 'OBJECT' and current_build(ctx) is not None

    def execute(self, ctx):
        discard_build(ctx, current_build(ctx)[TAG])
        self.report({'INFO'}, "Finalise discarded, originals shown")
        return {'FINISHED'}


# ------------------------------------------------------------------ UI

class FA_PT_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Finalise"
    bl_label = "Kitbash Finalise"

    def draw(self, ctx):
        lay = self.layout
        scene = ctx.scene
        col = current_build(ctx)
        lay.operator("fa.finalise", icon='MOD_BOOLEAN')
        lay.operator("fa.preview", icon='HIDE_OFF')
        row = lay.row(align=True)
        row.operator("fa.apply", icon='CHECKMARK')
        row.operator("fa.discard", icon='LOOP_BACK')
        if col is not None:
            lay.label(text=f"Draft: {col.name}", icon='OUTLINER_COLLECTION')
        box = lay.box()
        box.label(text="Connector (Part Sockets' Long peg sizes)")
        if ps_conn() is None:
            box.label(text="Part Sockets is not enabled", icon='ERROR')
        else:
            c = box.column(align=True)
            c.prop(scene, "fa_peg_profile")
            c.prop(scene, "fa_peg_side")
            props = ["ws_conn_scale", "ws_conn_size", "ws_conn_clearance", "ws_conn_bottom_gap"]
            props += ["ws_conn_oval"] if scene.fa_peg_profile == 'BAYONET' else ["ws_conn_taper"]
            for p in props:
                if hasattr(scene, p):
                    c.prop(scene, p)
            if getattr(scene, "ws_conn_size", "") == 'CUSTOM':
                c.prop(scene, "ws_conn_width")
                c.prop(scene, "ws_conn_length")
        box = lay.box()
        box.label(text="ID letter (one per model, set in Finalise)")
        c = box.column(align=True)
        c.prop(scene, "fa_letter_size")
        c.prop(scene, "fa_letter_depth")
        lay.label(text="Booleans: " + ("Hard Ops" if hops_bool() and (get_prefs() is None or get_prefs().use_hops)
                                       else "Blender Boolean") + ", Manifold solver")
        if scene.fa_last_log:
            box = lay.box()
            for line in scene.fa_last_log.splitlines()[-12:]:
                box.label(text=line)


class FA_Prefs(bpy.types.AddonPreferences):
    bl_idname = __name__
    use_hops: BoolProperty(name="Use Hard Ops booleans", default=True,
                           description="Boolean through Hard Ops' own setup when it is enabled "
                                       "(else plain Boolean modifiers set up the same way)")
    no_peg: StringProperty(name="No peg by default", default=DEFAULT_NO_PEG,
                           description="Joints whose piece starts with Peg off in the Finalise dialog "
                                       "(legs sit on their flat face and adaptors)")
    joint_order: StringProperty(name="Joint order", default=DEFAULT_ORDER,
                                description="Order parts are unioned into their piece, by the joint "
                                            "they sit on (side letters ignored)")

    def draw(self, ctx):
        self.layout.prop(self, "use_hops")
        self.layout.prop(self, "joint_order")
        self.layout.prop(self, "no_peg")


CLASSES = (FA_Item, FA_Bad, FA_OT_finalise, FA_OT_preview, FA_OT_apply, FA_OT_discard, FA_PT_panel, FA_Prefs)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    W, S = bpy.types.WindowManager, bpy.types.Scene
    W.fa_items = CollectionProperty(type=FA_Item)
    W.fa_bad = CollectionProperty(type=FA_Bad)
    W.fa_root = StringProperty()
    S.fa_peg_profile = EnumProperty(
        name="Peg", default='SQUARE',
        items=(('SQUARE', "Square (keyed)", "Part Sockets' push-fit peg made square with one corner cut off: "
                                            "it only goes in one way round, exactly as posed"),
               ('SPIKE', "Spike", "Part Sockets' basic push-fit connector: a round tapered peg with a "
                                  "lead-in nose, in a clearance cavity"),
               ('QUAD', "Quad-Key", "The spike with four flats: only seats every quarter turn"),
               ('BAYONET', "Bayonet", "Push in through the keyhole and twist a quarter turn to lock")),
        description="Connector at every joint where a piece comes off")
    S.fa_peg_side = EnumProperty(
        name="Peg On", default='AUTO',
        items=(('AUTO', "Piece (body if thin)", "The peg on the piece, the hole in the body - unless the body is too "
                                                "thin in the middle of the face for the hole (a hollow torso): then the "
                                                "peg goes on the body and the hole in the piece"),
               ('PIECE', "Always the piece", "The peg always on the piece, the hole always in the body (shortened "
                                              "where the body is thin)")),
        description="Which side of each joint gets the peg")
    S.fa_letter_size = FloatProperty(name="Max Letter Size", default=6.0, min=0.6, max=20.0,
                                     description="The ID letter fills each mating face up to this size (mm)")
    S.fa_letter_depth = FloatProperty(name="Letter Depth", default=0.2, min=0.05, max=1.0,
                                      description="How deep the letter is cut into each face (mm)")
    S.fa_last_log = StringProperty(options={'SKIP_SAVE'})


def unregister():
    W, S = bpy.types.WindowManager, bpy.types.Scene
    for p in ("fa_items", "fa_bad", "fa_root"):
        if hasattr(W, p):
            delattr(W, p)
    for p in ("fa_peg_profile", "fa_peg_side", "fa_letter_size", "fa_letter_depth", "fa_last_log"):
        if hasattr(S, p):
            delattr(S, p)
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
