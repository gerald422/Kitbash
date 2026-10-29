"""Torso on Vet / Bladeguard legs: match each AM-V2 legs' waist (plug + plating, around where Josh seats the torso) onto
the new legs and carry Josh's placement; compare with Mar Fil's export (kit) position."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, glob
from scipy.spatial import cKDTree
LJ = json.load(open('/home/claude/kits/legs_josh.json'))['legs']
S_WAIST = np.array(json.load(open('/home/claude/kits/amv2_partial.json'))['S_WAIST'])
def region_ref(rel, M, r=6.5, n=2500):
    V, T = geo.load(rel); S = geo.surf(V, T, 300000)
    j = (np.linalg.inv(M) @ np.r_[S_WAIST[:3, 3], 1])[:3]          # waist joint in the legs' coords
    k = (np.linalg.norm(S - j, axis=1) < r) & (S[:, 2] > j[2] - 4.5)
    R = S[k]; R = R[np.random.default_rng(0).choice(len(R), min(n, len(R)), replace=False)]
    return R, j
REFS = {rel: (np.array(v['M']),) + region_ref(rel, np.array(v['M'])) for rel, v in LJ.items() if 'Mirrored' not in rel}
def match(rel_new):
    V, T = geo.load(rel_new); S = geo.surf(V, T, 300000); tree = cKDTree(S)
    best = None
    for rref, (M, R, j) in REFS.items():
        # start: the reference region where it is in its own file, nudged to the new legs (same kit frame roughly)
        for dz in (0.0, 1.5, -1.5):
            R0, t0 = np.eye(3), np.array([0, 0, dz])
            Rg, tg, d = geo.icp(R, tree, S, R0, t0, 40)
            md = float(np.median(d))
            if best is None or md < best[0]:
                best = (md, rref, geo.M4(Rg, tg), M, j)
    md, rref, G, M, j = best
    Mnew = M @ np.linalg.inv(G)
    return md, rref, Mnew, G
if __name__ == '__main__':
    out = {}
    files = sorted(glob.glob(geo.RAW + 'VeteranSquad/VeteranSquad/Body/*/*.stl')) + sorted(glob.glob(geo.U + 'VeteranBladeSquad/VeteranBladeSquad/Body/*/*.stl'))
    for f in files:
        if 'Chest' in f: continue
        rel = f[len(geo.RAW):] if f.startswith(geo.RAW) else f[len(geo.U):]
        md, rref, Mnew, G = match(rel)
        # kit position = M identity; how far is the matched seat from it (at the waist joint)
        jt = S_WAIST[:3, 3]
        d_mm = np.linalg.norm((np.linalg.inv(Mnew) @ np.r_[jt, 1])[:3] - jt)
        out[rel] = dict(M=Mnew.tolist(), ref=rref, med=md)
        print('%-34s ref %-14s med %.3f | vs kit position: %.1f deg, %.2f mm at the waist' % (os.path.basename(rel), os.path.basename(rref)[:-4], md, geo.ang(Mnew[:3, :3]), d_mm), flush=True)
    json.dump(out, open('/home/claude/kits/legs_vet.json', 'w'), indent=1)
