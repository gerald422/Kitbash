import numpy as np
def section(V, T, axis, val):
    """segments where the mesh crosses the plane coordinate[axis] = val"""
    tri = V[T]; s = tri[:, :, axis] - val
    segs = []
    m = (s.min(1) < 0) & (s.max(1) > 0)
    for t, ss in zip(tri[m], s[m]):
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if (ss[i] < 0) != (ss[j] < 0):
                f = ss[i] / (ss[i] - ss[j]); pts.append(t[i] + f * (t[j] - t[i]))
        if len(pts) == 2: segs.append(pts)
    return np.array(segs)
