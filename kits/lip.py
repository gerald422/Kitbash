import geo, numpy as np, json, os
from scipy.spatial import cKDTree
A = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
W = {k: np.array(v) for k, v in json.load(open('/home/claude/kits/waist_frames2.json')).items()}
Vt, Tt = geo.load(A + 'Chest/23-Torso-2.stl'); St = geo.surf(Vt, Tt, 600000)
lip_t = St[(St[:, 1] > 3.0) & (St[:, 2] < 27.6) & (np.abs(St[:, 0]) < 4.5)]   # torso front bottom lip
REF = A + 'Legs/28-Legs-1.stl'
Vr, Tr = geo.load(REF); Sr = geo.surf(Vr, Tr, 600000)
d = cKDTree(lip_t).query(Sr)[0]
plate = Sr[(d < 2.5) & (Sr[:, 1] > 2.0)]                    # the stomach plating's top lip, in front
rng = np.random.default_rng(0)
plate = plate[rng.choice(len(plate), min(2500, len(plate)), replace=False)]
def seat(rel, iters=80):
    """Transform (torso coords <- legs raw) that puts this legs' stomach plating where 28-Legs-1's is."""
    V, T = geo.load(rel); S = geo.surf(V, T, 600000)
    M0 = W[REF] @ np.linalg.inv(W[rel])                     # plug line-up as the start
    # move the reference plate into the target legs' raw frame and ICP there
    Mi = np.linalg.inv(M0); src = plate @ Mi[:3, :3].T + Mi[:3, 3]
    tree = cKDTree(S)
    R, t, dd = geo.icp(src, tree, S, np.eye(3), np.zeros(3), iters, trim=0.9)
    D = geo.M4(R, t)                                          # ref plate (in target raw, via M0) -> target plate
    # legs raw -> torso:  x_t = M0 @ inv(D) @ x_raw
    return M0 @ np.linalg.inv(D), float(np.median(dd)), float(np.quantile(dd, 0.9))
if __name__ == '__main__':
    print('plate pts', len(plate), np.round(plate.min(0), 2), np.round(plate.max(0), 2))
    out = {}
    import glob
    for f in sorted(glob.glob(geo.RAW + A + 'Legs*/*.stl')) + sorted(glob.glob(geo.RAW + A + 'Legs*/Mirrored/*.stl')):
        rel = f.split(geo.RAW)[1]
        M, med, p90 = seat(rel)
        out[rel] = {'M': M.tolist(), 'med': med, 'p90': p90}
        print('%-26s med %.3f p90 %.3f  vs raw: rot %.2f move %s' % (os.path.basename(rel)[:-4], med, p90, geo.ang(M[:3, :3]), np.round(M[:3, 3], 2)))
    json.dump(out, open('/home/claude/kits/lip_seat.json', 'w'), indent=1)
