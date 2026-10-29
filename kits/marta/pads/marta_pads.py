import sys; sys.path.insert(0, '/home/claude/real')
import fitlib as F, numpy as np, json, glob, os
from scipy.spatial import cKDTree
U = "/mnt/user-data/uploads/new cults/"
P = json.load(open('/home/claude/real/pad_fits.json')); fit62 = np.array(P['_fit62'])
A = U + "All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL/"
V62, T62 = F.stl(A + "ShoulderPads/62-ShoulderPad-1.stl"); s62 = F.surf(V62, T62, 3000)
MX = F.MX
todo = sys.argv[1:]
outp = 'pad_fits_marta2.json'; out = json.load(open(outp)) if os.path.exists(outp) else {}
def match(src, tgt):
    tree = cKDTree(tgt); best = None
    for R0 in F.rots24():
        t0 = tgt.mean(0) - R0 @ src.mean(0); R, t, d = F.icp(src, tree, R0, t0, 20)
        if best is None or np.median(d) < best[0]: best = (np.median(d), R, t)
    R, t, d = F.icp(src, tree, best[1], best[2], 80)
    return F.pose(R, t), float(np.median(d)), float(np.quantile(d, .9))
for rel in todo:
    if rel in out: continue
    V, T = F.stl(U + rel); tgt = F.surf(V, T, 30000)
    G, med, p90 = match(s62, tgt)                       # as a right pad
    Gm, medm, p90m = match(s62, tgt * np.array([-1.0, 1, 1]))   # as a left pad (its mirror image is a right pad)
    fitR = fit62 @ np.linalg.inv(G); fitL = MX @ (fit62 @ np.linalg.inv(Gm)) @ MX
    out[rel] = dict(medR=med, p90R=p90, medL=medm, p90L=p90m, fitR=fitR.tolist(), fitL=fitL.tolist())
    print('%-60s R %.3f/%.3f  L %.3f/%.3f' % (rel[-60:], med, p90, medm, p90m), flush=True)
    json.dump(out, open(outp, 'w'), indent=1)
