import sys, numpy as np
sys.path.insert(0, '/home/claude/real'); import fitlib as F
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
z = np.load(SCR + "hand_grip.npz"); V, T = z["V"].astype(float), z["T"]
S = F.surf(V, T, 200000, 0)
c = np.array([-36.0, -62.91, 8.31]); ax = np.array([-1.0, 0, 0])
for it in range(4):
    h = (S - c) @ ax; lat = S - c - np.outer(h, ax); r = np.linalg.norm(lat, axis=1)
    k = (r < 2.2) & (h > -1.5)
    cs = []
    for zz in np.arange(-1.5, h[k].max(), 0.2):
        q = S[k & (np.abs(h - zz) < 0.08)]
        if len(q) > 20: cs.append(q.mean(0))
    cs = np.array(cs)
    if len(cs) > 3:
        u, s_, vt = np.linalg.svd(cs - cs.mean(0)); ax = vt[0] * np.sign(vt[0] @ ax); c = cs.mean(0)
h = (S - c) @ ax; lat = S - c - np.outer(h, ax); r = np.linalg.norm(lat, axis=1)
print("axis", ax.round(3), "c", c.round(2))
for zz in np.arange(-2.5, h[r < 2.5].max() + 0.01, 0.2):
    q = (np.abs(h - zz) < 0.06) & (r < 2.6)
    if q.sum() < 5: continue
    print("  h %5.2f n %4d r min %.2f med %.2f max %.2f" % (zz, q.sum(), r[q].min(), np.median(r[q]), r[q].max()))
