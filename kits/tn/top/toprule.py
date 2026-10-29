import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn'); sys.path.insert(0,'/home/claude/kits/cr/dev')
import numpy as np, json, stlcache, flats
from topface import merge_flats
from flatface import frame
import conv
QBI = np.linalg.inv(conv.Q['Back'])
SINK = 1.1
def pack_fit(V, T):
    M = merge_flats([(A, n, c) for A, n, c, o, s in flats.flats(V, T, min_area=0.5)])
    big = max([m for m in M if abs(m[1][2]) > 0.95], key=lambda m: m[0])
    P = frame(big[2], -big[1], [0, 1, 0])
    return QBI @ np.linalg.inv(P)
def forward_in_file(fit):
    """the model's forward (+Y of the Mar Fil frame) as a direction in the pack file, for a pack on S_AM Back"""
    W = conv.S_AM['Back'] @ fit; return np.linalg.inv(W)[:3, :3] @ np.array([0, 1, 0.])
def back_top(V, fwd):
    """top-centre of a flat-lying pack (up +Y): origin on the top surface, Z up, Y forward (made level)"""
    xc = (V[:, 0].min() + V[:, 0].max()) / 2
    col = V[np.abs(V[:, 0] - xc) < 0.6]
    ymax = col[:, 1].max(); band = col[col[:, 1] > ymax - 0.3]
    zc = (band[:, 2].min() + band[:, 2].max()) / 2
    near = col[np.abs(col[:, 2] - zc) < 0.6]; yt = near[:, 1].max()
    f = np.array(fwd, float); f[1] = 0; f /= np.linalg.norm(f)
    return frame(np.array([xc, yt, zc]), np.array([0, 1., 0]), f)
def topper_frame(V, front=np.array([0, 0, 1.])):
    """pole tip = lowest point (up +Y); mount SINK above the tip on the pole axis; Z up, Y = front"""
    y0 = V[:, 1].min(); tip = V[V[:, 1] < y0 + 0.2]
    c = tip.mean(0)
    return frame(np.array([c[0], y0 + SINK, c[2]]), np.array([0, 1., 0]), front)
