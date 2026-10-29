"""For every staged Springles arm file: the shoulder disc in file coords (largest flat facing +-X/+-Y, area 12-20)."""
import sys, json, numpy as np, glob, os
sys.path.insert(0, "/home/claude/blend/forclaude")
from stl_io import read_stl
from disc2 import disc
U = "/mnt/user-data/uploads/new cults/Springles/"
out = {}
for f in sorted(glob.glob(U + "pattern? arms/*/*.stl")):
    rel = os.path.relpath(f, U); v, n, t = read_stl(f); V = np.asarray(v, float); T = np.asarray(t)
    best = None
    for nref in ([1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]):
        nref = np.array(nref, float)
        # near = the extreme of the mesh in -nref direction ... search whole mesh: near = bbox centre, big radius
        d = disc(V, T, nref, V.mean(0), cos=0.999, rad=40)
        if d and (best is None or d["area"] > best[1]["area"]): best = (nref, d)
    nref, d = best
    out[rel] = dict(n=nref.tolist(), area=d["area"], centroid=d["centroid"].tolist(), r=d["r"], spread=d["spread"])
    print("%-62s n %-16s area %5.1f r %.2f sp %.3f" % (rel[:62], nref.astype(int).tolist(), d["area"], d["r"], d["spread"]))
json.dump(out, open("discs_files.json", "w"), indent=0)
