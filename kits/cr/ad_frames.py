import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr')
import numpy as np, json, stlcache, geo, disc
from scipy.spatial import cKDTree
D = "/mnt/user-data/uploads/new cults/body adaptor/"
LJ = json.load(open('/home/claude/kits/legs_josh.json'))['legs']
SW = np.array(json.load(open('/home/claude/kits/amv2_partial.json'))['S_WAIST'])
r = json.load(open('ad_match.json'))['1']
G = geo.M4(np.array(r['R']), np.array(r['t'])); j = np.array(r['j'])
Tj = np.eye(4); Tj[:3, 3] = j
M_ad = np.array(LJ[r['ref']]['M']) @ Tj @ np.linalg.inv(G)      # adaptor coords -> kit
print('M_ad\n', M_ad.round(3))
# other adaptors vs 1
V1, T1 = stlcache.load(D + "lower_body_(torso)_1.stl"); S1 = geo.surf(V1, T1, 200000); tr = cKDTree(S1)
for i in range(2, 7):
    V, T = stlcache.load(D + f"lower_body_(torso)_{i}.stl"); P = geo.surf(V, T, 4000)
    R, t, d = geo.icp(P, tr, S1, np.eye(3), np.zeros(3), 40)
    print(i, 'vs 1: med %.3f  rot %.2f deg  t %s' % (np.median(d), geo.ang(R), t.round(3)))
# ring plane + axis centre on adaptor 1
cen, n, a = disc.tri_info(V1, T1)
k = (n[:, 1] > 0.97) & (np.abs(cen[:, 1] - 4.5) < 0.25)
ring_y = (cen[k, 1] * a[k]).sum() / a[k].sum()
print('ring y %.3f area %.2f' % (ring_y, a[k].sum()))
# axis centre: circle fit of the body section at y 2.5..4.0 outer surface is not round (ribs) -> use dome sphere centre x,z
kd = cen[:, 1] > 4.9; P = cen[kd]
Am = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); x = np.linalg.lstsq(Am, b, rcond=None)[0]
print('dome centre', x[:3].round(3))
json.dump({'M_ad': M_ad.tolist(), 'ring_y': float(ring_y), 'dome_c': x[:3].tolist()}, open('ad_frames.json', 'w'))
