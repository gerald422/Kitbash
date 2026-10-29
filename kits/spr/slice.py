import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/real'); import fitlib as F
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
z = np.load(SCR + "hand_grip_big.npz"); V, T = z["V"].astype(float), z["T"]
S = F.surf(V, T, 400000, 0)
fig, ax = plt.subplots(1, 3, figsize=(15, 5))
c = S.mean(0)
for i, (u, w, n, lab) in enumerate([(0, 2, 1, "x-z (slice y)"), (0, 1, 2, "x-y (slice z)"), (1, 2, 0, "y-z (slice x)")]):
    # slice through the cap region centre
    cc = np.array([-52.3, -63.05, 6.1])
    k = np.abs(S[:, n] - cc[n]) < 0.04
    ax[i].scatter(S[k, u], S[k, w], s=0.5); ax[i].set_aspect("equal"); ax[i].set_title(lab); ax[i].grid(True)
plt.savefig("rh3/slices.png", dpi=90)
print(S.min(0), S.max(0))
