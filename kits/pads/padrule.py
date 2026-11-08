"""Pad seat by rule: Josh's 62-on-76 seat turned about the shoulder axis (torso X through the shoulder joint)
by the arm's swing, then pushed out along the seat's outward axis until 62 clears the arm. Right side; lefts mirrored."""
import sys, json, math, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads")
from kb import *
from scipy.spatial import cKDTree
TOR = BY["MarFil Assault - Torso 1"]
J = sock(TOR, "Shoulder R")[:3, 3]
P62 = BY["MarFil Assault - Shoulder Pad 1"]; F62 = fit(P62, "Pad R"); V62, T62 = prev(P62)
A76 = BY["MarFil Assault - Arm 1A R"]
def arm_world(a):
    side = "R" if fit(a, "Shoulder R") is not None else "L"
    S = sock(TOR, "Shoulder " + side) @ fit(a, "Shoulder " + side)
    V, T = prev(a); V = xf(S, V)
    if side == "L": V = V * [-1, 1, 1]; T = T[:, ::-1]; S = conj(S)
    return side, S, V, T
def upper_dir(V):
    d = np.linalg.norm(V - J, axis=1); r = d.max()
    band = V[(d > 0.35 * r) & (d < 0.65 * r)]
    u = band.mean(0) - J; u[0] = 0.0                 # in the plane the arm swings in (torso Y-Z)
    return u / np.linalg.norm(u), r
def rx(phi):
    c, s = math.cos(phi), math.sin(phi); R = np.eye(4); R[1:3, 1:3] = [[c, -s], [s, c]]; return R
def about_J(R): return np.block([[np.eye(3), J[:, None]], [np.zeros((1, 3)), np.ones((1, 1))]]) @ R @ np.block([[np.eye(3), -J[:, None]], [np.zeros((1, 3)), np.ones((1, 1))]])
_, S76, V76, _ = arm_world(A76)
SEAT76 = S76 @ sock(A76, "Pad R")                   # Pad socket (62 convention) in the torso frame
U76, _ = upper_dir(V76)
def normals(V, T):
    n = np.zeros_like(V); f = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    for k in range(3): np.add.at(n, T[:, k], f)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
def inside_frac(Pp, V, N, tree):
    d, i = tree.query(Pp); s = np.einsum("ij,ij->i", Pp - V[i], N[i])
    return float(((s < 0) & (d < 1.5)).mean()), d
def seat(a, push=True):
    side, S, V, T = arm_world(a)
    u, r = upper_dir(V)
    phi = math.atan2(np.cross(U76, u)[0], U76 @ u)
    W = about_J(rx(phi)) @ SEAT76
    moved = 0.0
    if push:
        N = normals(V, T); tree = cKDTree(V)
        out = (xf(W @ F62, V62).mean(0) - J); out /= np.linalg.norm(out)
        for k in range(40):
            Pp = xf(W @ F62, V62)
            f, d = inside_frac(Pp, V, N, tree)
            if f <= 0.01: break
            W = np.eye(4) @ W; W[:3, 3] += out * 0.1; moved += 0.1
    return side, S, W, math.degrees(phi), moved
