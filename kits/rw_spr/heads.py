"""Helmets -> Neck: Josh's Assault helmet 1 (its whole shape, then its neck ring) matched onto each helmet, carrying
his Neck fit across (kits/neckfit.py, with 12 turns about Z because these files lie at any heading on the plate)."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/rw_spr"); from common import *
AMH = "Mar Fil - Tacticus/AssaultMarines-V2/Helmet-Heads/Heads/MarFil Assault - Helmet 1"
Va, Ta = F.stl(LIBU + AMH + ".stl"); Va = np.asarray(Va, float)
F_AMH = np.array(lib_sidecar(AMH + ".sockets.json")["fits"]["Neck"]).reshape(4, 4)
S = geo.surf(Va, Ta, 200000); rng = np.random.default_rng(1)
FULL = S[rng.choice(len(S), 3000, replace=False)]
NECK = np.linalg.inv(F_AMH)[:3, 3]; REG = S[np.linalg.norm(S - NECK, axis=1) < 4.0]
STARTS = [rz(np.radians(a)) for a in range(0, 360, 30)]
def neck_fit(V, T):
    Q = geo.surf(V, T, 80000)
    m, R, t = icp_starts(FULL, REG, Q, STARTS)
    return F_AMH @ np.linalg.inv(M4(R, t)), m
if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1])); out = json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else {}
    jobs = [j for j in jobs if j[0] not in out]
    for rel, scale in jobs:
        V, T = load(rel, scale); Fn, m = neck_fit(V, T); out[rel] = dict(fit=flat(Fn), med=m, scale=scale)
        print("%-70s match %.3f" % (rel[-70:], m), flush=True)
        json.dump(out, open(sys.argv[2], "w"), indent=0)          # after each helmet, so a stop loses nothing
