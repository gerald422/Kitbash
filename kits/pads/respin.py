"""Turn a Pad seat about its outward axis (62/56 cup centre -> pad) so its spin matches the target."""
import sys, json, math, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); from spin import *
def axis_rot(o, t):
    o = o / np.linalg.norm(o); K = np.array([[0, -o[2], o[1]], [o[2], 0, -o[0]], [-o[1], o[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K
def respin(seat, target_off):
    """seat (torso frame) -> seat with spin offset target_off (deg, relative to SP0), turned about the cup axis."""
    c, o = axes(seat); cur = dspin(spin_of(seat)); t = math.radians(target_off - cur)
    R = axis_rot(o, t); W = np.eye(4); W[:3, :3] = R @ seat[:3, :3]; W[:3, 3] = R @ (seat[:3, 3] - c) + c
    return W
