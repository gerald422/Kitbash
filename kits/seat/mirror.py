"""Left and right, inside Blender (skill `kitbash-seat-by-shape`; moved from the Nov 23 cloth_flip).
Right parts are placed; a left part is its right one mirrored (docs/PLAN.md, Mirroring).
  twist_check  a left arm sculpt in a right slot shows as the elbow bending backwards: try it turned 180 deg about the
               upper arm through the shoulder pivot and compare the clashes (pad in arm, arm in torso)
  mirror_live  show the left side live: a Mirror modifier across the torso's own X = 0 plane (batch files)"""
import math
import numpy as np
from mathutils import Matrix, Vector
import geom as G
from pads import CROWN


def upper_arm(arm, guide):
    """(pivot = the guide's dome centre, unit upper-arm direction: arm vertices 5-10 mm from the pivot)"""
    A = np.array(guide.matrix_world); piv = A[:3, 3] - CROWN * A[:3, 2] / np.linalg.norm(A[:3, 2])
    V = G.verts_world(arm); d = np.linalg.norm(V - piv, axis=1); ua = (V[(d > 5) & (d < 10)] - piv).mean(0)
    return piv, ua / np.linalg.norm(ua)


def twist_check(arm, guide, torso, twists=(0, 180)):
    """per twist (deg about the upper arm): pad-in-arm and arm-in-torso shares. Leaves the arm as it was."""
    pad = next(o for o in guide.children if o.type == 'MESH'); piv, ua = upper_arm(arm, guide)
    M0 = arm.matrix_world.copy(); pv = Vector(piv.tolist()); bt = G.bvh(torso); out = []
    P = G.verts_world(pad); P = P[np.random.default_rng(0).choice(len(P), min(2000, len(P)), replace=False)]
    for a in twists:
        M = Matrix.Translation(pv) @ Matrix.Rotation(math.radians(a), 4, Vector(ua.tolist())) @ Matrix.Translation(-pv) @ M0
        VA = G.verts_world(arm, M); ba = G.bvh(arm, VA); Q = VA[np.random.default_rng(1).choice(len(VA), min(3000, len(VA)), replace=False)]
        out.append(dict(twist=a, pad_in_arm=round(G.inside_share(ba, P), 3), arm_in_torso=round(G.inside_share(bt, Q), 3)))
    arm.matrix_world = M0
    return out


def twist(arm, guide, deg=180):
    """turn the arm deg about its upper arm through the shoulder pivot"""
    piv, ua = upper_arm(arm, guide); pv = Vector(piv.tolist())
    arm.matrix_world = Matrix.Translation(pv) @ Matrix.Rotation(math.radians(deg), 4, Vector(ua.tolist())) @ Matrix.Translation(-pv) @ arm.matrix_world


def mirror_live(o, torso, name="Left (mirror)"):
    """a Mirror modifier showing o's left copy across the torso's X = 0 plane (mesh only, transforms untouched)"""
    m = o.modifiers.new(name, 'MIRROR'); m.use_axis = (True, False, False); m.mirror_object = torso
    m.use_mirror_merge = False; m.use_clip = False; m.use_bisect_axis = (False, False, False)
    return m
