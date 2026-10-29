import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, sys
D = np.load("slices.npz")
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
if __name__ == "__main__":
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.5))
    for ax, yv in zip(axs, (-1.5, 0.0, 1.5)):
        for key, col in (("torso", "0.6"), ("arm", "tab:blue"), ("pad", "tab:orange")):
            S = section(D[key + "_v"], D[key + "_t"], 1, yv)
            for a, b in S: ax.plot([a[0], b[0]], [a[2], b[2]], color=col, lw=0.6)
        pa = D["padA"]; ax.plot(pa[0, 3], pa[2, 3], "r+", ms=12)
        ax.plot(0, 0, "kx", ms=10)
        ax.set_aspect("equal"); ax.set_xlim(-8, 10); ax.set_ylim(-9, 13); ax.grid(alpha=0.3)
        ax.set_title(f"slice y={yv} (shoulder frame: x out, z up)")
    plt.tight_layout(); plt.savefig(sys.argv[1] if len(sys.argv) > 1 else "slices.png", dpi=80)
