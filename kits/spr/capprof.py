import numpy as np, sys
sys.path.insert(0, '/home/claude/real'); import fitlib as F
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
def profile(S, c, ax, lo=-2.5, hi=0.6, step=0.1):
    h = (S - c) @ ax; lat = S - c - np.outer(h, ax); r = np.linalg.norm(lat, axis=1)
    for zz in np.arange(lo, hi, step):
        q = (np.abs(h - zz) < 0.04) & (r < 3)
        if q.sum() < 5: continue
        print("  h %5.2f n %4d r min %.2f med %.2f max %.2f" % (zz, q.sum(), r[q].min(), np.median(r[q]), r[q].max()))
def end_axis(S, ax0, depth=0.8):
    """cap at the end of S along ax0: points within `depth` of the extreme; centre = circle centre of the rim, refine axis
    so the cap's rim is level"""
    ax = ax0 / np.linalg.norm(ax0)
    for it in range(8):
        h = S @ ax; top = h.max(); P = S[h > top - depth]
        c = P.mean(0)
        # axis = direction of symmetry: normal of best plane through the rim ring (points at the largest radius)
        lat = P - c - np.outer((P - c) @ ax, ax); r = np.linalg.norm(lat, axis=1)
        ring = P[r > np.quantile(r, 0.7)]
        cc = ring.mean(0); u, s, vt = np.linalg.svd(ring - cc); n = vt[2] * np.sign(vt[2] @ ax)
        ax = n
    return cc, ax, top
z = np.load(SCR + "hand_grip_big.npz"); V, T = z["V"].astype(float), z["T"]; S = F.surf(V, T, 150000, 0)
c, ax, top = end_axis(S, np.array([-1.0, 0, 0]))
print("hand_grip cap centre", c.round(3), "axis", ax.round(3))
profile(S, c, ax)
