import geo, numpy as np, json, os, sys, disc
from scipy.spatial import cKDTree
A = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
W = {k: np.array(v) for k, v in json.load(open('/home/claude/kits/waist_frames2.json')).items()}
Vt, Tt = geo.load(A + 'Chest/23-Torso-2.stl'); St = geo.surf(Vt, Tt, 600000)
lip_t = St[(St[:, 1] > 3.0) & (St[:, 2] < 27.6) & (np.abs(St[:, 0]) < 4.5)]
REF = A + 'Legs/28-Legs-1.stl'
Vr, Tr = geo.load(REF)
cen, n, a = disc.tri_info(Vr.astype(float), Tr)
Sr = geo.surf(Vr, Tr, 600000)
d = cKDTree(lip_t).query(Sr)[0]
rng = np.random.default_rng(0)
plate = Sr[(d < 2.5) & (Sr[:, 1] > 2.0)]; plate = plate[rng.choice(len(plate), min(2000, len(plate)), replace=False)]
P = W[REF]; L = (cen - P[:3, 3]) @ P[:3, :3]; nl = n @ P[:3, :3]
fl = (np.abs(nl[:, 0]) > 0.97) & (L[:, 2] < -0.2) & (L[:, 2] > -2.8) & (np.abs(L[:, 1]) < 2.5) & (np.abs(L[:, 0]) > 2.5) & (np.abs(L[:, 0]) < 4.5)
flats = cen[fl]
# densify flats by sampling their triangles
idx = np.where(fl)[0]
tri = Vr[Tr[idx]].astype(float); ar = a[idx]
k = rng.choice(len(idx), 2000, p=ar / ar.sum()); u, v = rng.random(2000), rng.random(2000); m = u + v > 1; u[m], v[m] = 1 - u[m], 1 - v[m]
flats = tri[k, 0] + u[:, None] * (tri[k, 1] - tri[k, 0]) + v[:, None] * (tri[k, 2] - tri[k, 0])
REG = np.vstack([plate, flats])
def seat(rel, iters=100):
    V, T = geo.load(rel); S = geo.surf(V, T, 600000)
    M0 = W[REF] @ np.linalg.inv(W[rel])
    Mi = np.linalg.inv(M0); src = REG @ Mi[:3, :3].T + Mi[:3, 3]
    R, t, dd = geo.icp(src, cKDTree(S), S, np.eye(3), np.zeros(3), iters, trim=0.9)
    D = geo.M4(R, t)
    dp = dd[:len(plate)]; df = dd[len(plate):]
    return M0 @ np.linalg.inv(D), float(np.median(dp)), float(np.median(df))
if __name__ == '__main__':
    print('plate', len(plate), 'flats', len(flats), 'flat area', ar.sum())
    import glob
    out = {}
    for f in sorted(glob.glob(geo.RAW + A + 'Legs*/*.stl')) + sorted(glob.glob(geo.RAW + A + 'Legs*/Mirrored/*.stl')):
        rel = f.split(geo.RAW)[1]
        M, mp, mf = seat(rel)
        L0 = json.load(open('/home/claude/kits/lip_seat.json'))[rel]['M']
        out[rel] = {'M': M.tolist(), 'plate': mp, 'flats': mf}
        print('%-26s plate %.3f flats %.3f  vs raw rot %6.2f  vs plate-only %5.2f deg' % (os.path.basename(rel)[:-4], mp, mf, geo.ang(M[:3, :3]), geo.ang(M[:3, :3] @ np.array(L0)[:3, :3].T)))
    json.dump(out, open('/home/claude/kits/lip_seat2.json', 'w'), indent=1)
