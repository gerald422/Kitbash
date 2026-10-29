import numpy as np
AX_Y, AX_Z = 0.2, 31.95
def inner_x(V, side, around=None, r=1.5, window=4.0):
    """x of the arm's inner face on the shoulder axis (y=0.2, z=31.95): the innermost vertex within r of the axis.
    side R: the arm lies at +x of the joint, inner face = min x. around: limit to |x-around|<window."""
    V = np.asarray(V, float)
    k = np.hypot(V[:, 1] - AX_Y, V[:, 2] - AX_Z) < r
    if around is not None: k &= np.abs(V[:, 0] - around) < window
    if not k.any(): return None
    return (V[k, 0].min() + 0.06) if side == 'R' else (V[k, 0].max() - 0.06)
