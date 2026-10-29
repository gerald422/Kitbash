import numpy as np, matplotlib, sys, json; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "/home/claude/blend/forclaude"); from stl_io import read_stl
from slice_plot import section
D = "/home/claude/liblift_v3/Mar Fil - Tacticus/AssaultMarines-V2/Arms/"
pairs = [("111-Arm-8-R-A", "112-Arm-8-R-B"), ("101-Arm-6-R-A", "102-Arm-6-R-B"), ("76-Arm-1-R-A", "77-Arm-1-R-B")]
fig, axs = plt.subplots(2, 3, figsize=(15, 10))
for col, (a, b) in enumerate(pairs):
    for row, yv in enumerate((0.0, 1.5)):
        ax = axs[row, col]
        for name, c in ((a, "tab:blue"), (b, "tab:red")):
            V, N, T = read_stl(D + name + ".stl")
            for p, q in section(V, T, 1, yv): ax.plot([p[0], q[0]], [p[2], q[2]], color=c, lw=0.6)
        ax.plot(0, 0, "kx"); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_title(f"{a} (blue) vs {b} (red), y={yv}")
        ax.set_xlim(-4, 9); ax.set_ylim(-10, 7)
plt.tight_layout(); plt.savefig("ab.png", dpi=70)
for n in ("111-Arm-8-R-A", "112-Arm-8-R-B"):
    print(n, json.load(open(D + n + ".sockets.json")).get("sockets", "")[:2] if False else open(D + n + ".sockets.json").read()[:600])
