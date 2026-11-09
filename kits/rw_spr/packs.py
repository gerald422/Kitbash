"""Springles vox backpacks -> Back: the mount plate on the AM torso's back face, plate centres together (Turtle Ninja's
pack rule, kits/tn/packs_try.py). The packs stand upright with the mount side towards -Y (the cog-and-vents side is +Y);
the plate = the frontmost band of the pack (within 0.4 mm of its most -Y point: the upper connector plate with the
springs), its centre on the back face's centre."""
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/rw_spr"); from common import *
import flats, conv
from flatface import frame
QBI = np.linalg.inv(conv.Q["Back"])
def pack_fit(V, T):
    S = geo.surf(V, T, 200000)
    w = np.array([np.ptp(S[np.abs(S[:, 2] - z) < 0.5, 0]) if (np.abs(S[:, 2] - z) < 0.5).any() else 0 for z in np.arange(0, S[:, 2].max(), 0.5)])
    top = 0.5 * int(np.argmax(w < 3.0) if (w < 3.0).any() else len(w))          # where the aerial starts
    body = S[S[:, 2] < top]; ymin = body[:, 1].min(); band = body[body[:, 1] < ymin + 0.4]
    c = np.array([0.5 * (band[:, 0].min() + band[:, 0].max()), ymin, band[:, 2].mean()])
    P = frame(c, [0, 1.0, 0], [0, 0, 1.0])
    return QBI @ np.linalg.inv(P), "mount plate = frontmost band (-Y) of the body below the aerial (z<%.1f), centre x %.2f z %.2f" % (top, c[0], c[2])
if __name__ == "__main__":
    import os
    D = "Springles/accessorys and equipment/vox backpacks/"; out = {}
    for f in sorted(os.listdir(U + D)):
        if not f.endswith(".stl"): continue
        V, T = load(D + f, SPR_SCALE); Fit, note = pack_fit(V, T)
        out[D + f] = dict(fit=flat(Fit), note=note, scale=SPR_SCALE); print(f, note)
    json.dump(out, open(sys.argv[1], "w"), indent=0)
