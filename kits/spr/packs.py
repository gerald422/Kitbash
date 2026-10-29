"""Springles heavy-weapon backpacks (and the assault cannon ammo pack): mount plate (A~50 flat facing the torso, file -Y)
on the Back socket, plate centres together (same rule as Turtle Ninja's packs)."""
import sys, json, glob, os, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/kits')
import stlcache, flats, conv
from flatface import frame
U = "/mnt/user-data/uploads/new cults/Springles/"
K = 1.1
def pack_fit(rel):
    V, T = stlcache.load(U + rel); V = V * K
    F = flats.flats(V, T, min_area=20.0)
    plate = max([f for f in F if f[1][1] < -0.98], key=lambda f: f[0])
    A, n, c = plate[0], plate[1], plate[2]
    Fp = np.linalg.inv(conv.Q['Back']) @ np.linalg.inv(frame(c, -n, [0, 0, 1.0]))
    return Fp, A, c
if __name__ == "__main__":
    out = {}
    for p in sorted(glob.glob(U + "heavy weapons/backpacks/*.stl")) + [U + "assault cannon/assault cannon ammo pack.stl"]:
        rel = os.path.relpath(p, U)
        if "camera" in rel: continue
        Fp, A, c = pack_fit(rel); out[rel] = dict(fit=Fp.tolist(), plate=A)
        print("%-55s plate %.1f" % (rel, A))
    json.dump(out, open("w/packs.json", "w"), indent=0)
