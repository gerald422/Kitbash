import numpy as np, pickle
from scipy.spatial.transform import Rotation as R
TJ = pickle.load(open('tab_josh.pkl', 'rb')); fits = {}
for nm, r in TJ.items():
    k = float(r['scale'].mean()); S = np.diag([k, k, k, 1.0])
    F = np.linalg.inv(r['A']) @ r['P1'] @ np.linalg.inv(S)          # sidecar convention: mesh scaled by k, then socket @ fit
    U, s, Vt = np.linalg.svd(F[:3, :3]); print('%s: scale %.3f, fit rigid to %.1e; fit origin (tabard top, in the tabard-spot frame) %s' % (nm, k, np.abs(s - 1).max(), (np.linalg.inv(F) @ [0, 0, 0, 1])[:3].round(2)))
    fits[r['loin']] = dict(fit=F, scale=k)
pickle.dump(fits, open('tab_fits.pkl', 'wb'))
