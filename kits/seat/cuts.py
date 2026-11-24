"""Cuts taken from seats (no hand cutting), inside Blender. Moved from the Nov 23 scripts (cut_take, cut_take_arms).
A cut is a copy of the part's own faces in the region the method matches, parented to the part with identity local
(it shares the part's frame, like the reference's cuts), plus kb_ props saying what it stands for.
  arm pad spot: the arm faces the pad sees from inside its guide (first ray hits from the dome centre, CROWN mm under
                the crown, within 75 deg of the guide axis, plus one ring); the guide's pose on the arm is kept on the
                cut as kb_adapter_in_arm
  legs waist:   the waist block under the waist-top flat (h -5..+0.6 mm, r < 9 mm)"""
import math
import numpy as np
import bpy
from mathutils import Matrix, Vector
import geom as G
from pads import CROWN, CONE


def part_cut(part, poly_idx, name, coll, props):
    me = part.data; polys = [me.polygons[i] for i in sorted(set(poly_idx))]
    vids = sorted({v for p in polys for v in p.vertices}); remap = {v: k for k, v in enumerate(vids)}
    m = bpy.data.meshes.new(name); m.from_pydata([tuple(me.vertices[v].co) for v in vids], [], [[remap[v] for v in p.vertices] for p in polys]); m.update()
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old)
    o = bpy.data.objects.new(name, m); coll.objects.link(o)
    o.parent = part; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = Matrix.Identity(4)
    for k, v in props.items(): o[k] = v
    o.color = (0.2, 0.75, 0.3, 1); o.display_type = 'SOLID'
    return o, len(polys)


def grow(me, idx, rings=1):
    s = set(idx); v2p = {}
    for p in me.polygons:
        for v in p.vertices: v2p.setdefault(v, []).append(p.index)
    for _ in range(rings):
        vs = {v for i in s for v in me.polygons[i].vertices}; s |= {p for v in vs for p in v2p[v]}
    return s


def pad_spot_cut(arm, guide, coll, source="seat"):
    """the arm's pad spot cut from its guide's current seat"""
    mw = arm.matrix_world; b = G.bvh(arm)
    M = np.array(guide.matrix_world); ax = M[:3, 2] / np.linalg.norm(M[:3, 2]); c = M[:3, 3] - CROWN * ax
    x = np.cross([0.31, 0.71, 0.63], ax); x /= np.linalg.norm(x); y = np.cross(ax, x); hit = set()
    for th in np.radians(np.arange(0, CONE + 0.1, 1.5)):
        for ph in np.radians(np.arange(0, 360, 3 if th > 0 else 360)):
            u = math.cos(th) * ax + math.sin(th) * (math.cos(ph) * x + math.sin(ph) * y)
            loc, nor, i, _d = b.ray_cast(Vector(c + u * 30), Vector(-u), 40.0)
            if loc is not None and nor.dot(Vector(u)) > 0: hit.add(i)
    hit = grow(arm.data, hit, 1)
    rel = mw.inverted() @ guide.matrix_world
    return part_cut(arm, hit, (arm.name + " - pad spot cut (auto)")[:63], coll,
                    dict(kb_cut_of=arm.name, kb_joint="Pad (pauldron adapter)",
                         kb_how="arm faces the pad sees from inside: first ray hits within 75 deg of the pad axis, +1 ring",
                         kb_adapter_in_arm=[v for row in rel for v in row], kb_from=source))


def legs_waist_cut(legs, c0, n0, coll, name, frame=None, source="seat"):
    """the legs' waist cut: faces of the waist block under the flat (c0 / n0 in `frame`, a world 4x4; default world)"""
    F = np.eye(4) if frame is None else G.M4(frame)
    Mi = np.linalg.inv(F) @ np.array(legs.matrix_world)
    V = G.verts_local(legs) @ Mi[:3, :3].T + Mi[:3, 3]; c0, n0 = np.asarray(c0), np.asarray(n0)
    h = (V - c0) @ n0; r = np.linalg.norm((V - c0) - np.outer(h, n0), axis=1); inside = (h < 0.6) & (h > -5.0) & (r < 9.0)
    pidx = [p.index for p in legs.data.polygons if all(inside[v] for v in p.vertices)]
    return part_cut(legs, pidx, name[:63], coll,
                    dict(kb_cut_of=legs.name, kb_joint="Waist (flat-topped legs, adapter 3)", kb_how="faces within -5..+0.6 mm of the waist-top flat, r < 9 mm",
                         kb_flat_c=list(map(float, c0)), kb_flat_n=list(map(float, n0)), kb_seat_torso_frame=G.flat16(Mi), kb_from=source))
