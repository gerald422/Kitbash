"""Shoulder rotation of every Springles arm relative to the reference (slung arm), in right-arm torso space. Cached."""
import sys, json, os, numpy as np
import capmatch as CM, spr_pads2 as PA
AF = sorted(json.load(open("arm_fits.json")))
part, nparts = int(sys.argv[1]), int(sys.argv[2])
SR = PA.ref()[0]
fn = "w/swing_%d.json" % part
import os
out = json.load(open(fn)) if os.path.exists(fn) else {}
for i, rel in enumerate(AF):
    if i % nparts != part or rel in out: continue
    side, W, P = CM.torso_pts(rel); S = CM.shoulder(P)
    th, med = CM.match(SR, S); R3, m3 = CM.match3(SR, S, th)
    if m3 > 0.15:
        Ra, ma = CM.match_any(SR, S)
        if ma < m3: R3, m3 = Ra, ma
    out[rel] = dict(side=side, R=R3.tolist(), median=m3, swing1=th)
    json.dump(out, open(fn, "w")); print(rel, round(m3, 3), flush=True)
print("PART-DONE")
