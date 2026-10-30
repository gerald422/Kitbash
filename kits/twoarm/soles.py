import json, struct, sys, numpy as np, re
from collections import defaultdict
B = sys.argv[1]
d = json.load(open(B + "/index.json"))
def V(p):
    b = open(B + "/" + p["prev"], "rb").read(); nv = struct.unpack_from("<I", b, 4)[0]
    return np.frombuffer(b, np.float32, nv * 3, 12).reshape(-1, 3).astype(float)
M4 = lambda a: np.array(a, float).reshape(4, 4)
out = defaultdict(list)
for p in d["parts"]:
    if p["type"] != "Legs" or p["maker"] not in ("MarFil", "Marta") or not p.get("prev"): continue
    if re.search(r"kneel|sit|crouch|bike|ride", p["name"], re.I): continue
    s = next((x for x in p["sockets"] if x["t"] == "Base"), None)
    if s is None: continue
    S = M4(s["m"]); w = (V(p) - S[:3, 3]) @ S[:3, :3]
    z0 = w[:, 2].min()
    # each foot: the boot below 2.5 mm, split in two along the widest direction
    boot = w[w[:, 2] < z0 + 2.5]
    c = boot[:, :2] - boot[:, :2].mean(0); u = np.linalg.svd(c, full_matrices=False)[2][0]
    pr = c @ u; g = np.sort(pr); dg = np.diff(g); i = np.argmax(dg)
    if dg[i] < 2.0: continue
    for f in (boot[pr <= g[i]], boot[pr > g[i]]):
        if f[:, 2].min() > z0 + 0.3: continue           # a raised foot
        q = f[:, :2] - f[:, :2].mean(0); a = np.linalg.svd(q, full_matrices=False)[2]
        L, W = np.ptp(q @ a[0]), np.ptp(q @ a[1])
        out[p["maker"]].append((L, W))
for m, a in out.items():
    a = np.array(a); print(m, "feet", len(a), "boot length median %.2f (p25 %.2f p75 %.2f)  width median %.2f (p25 %.2f p75 %.2f)" % (np.median(a[:, 0]), *np.percentile(a[:, 0], [25, 75]), np.median(a[:, 1]), *np.percentile(a[:, 1], [25, 75])))
