import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/real')
import geo, fitlib as F
from scipy.spatial import cKDTree
REL = 'CaptainWithJumpPack/CaptainWithJumpPack/RawStl/'
V, T = geo.load(REL + '3-Legs.stl'); print('body bbox', V.min(0).round(1), V.max(0).round(1))
for f in ('8-WaistPlate-1', '10-WaistPlate-3', '11-Relic', '6-Plate', '7-Cape', '4-JumpPack'):
    v, t = geo.load(REL + f + '.stl'); print('%-16s bbox %s %s' % (f, v.min(0).round(1), v.max(0).round(1)))
# the AM torso (torso coordinates = its own file) onto the body's chest
Vt, Tt = F.stl('/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 3.stl')
src = geo.surf(Vt, Tt, 4000); S = geo.surf(V, T, 300000); tree = cKDTree(S)
best = None
for dz in np.arange(-6, 14, 2.0):
    for dy in (-2, 0, 2):
        R, t, d = geo.icp(src, tree, S, np.eye(3), np.array([0, dy, dz]), 40)
        m = float(np.median(d))
        if best is None or m < best[0]: best = (m, R, t)
m, R, t = best
print('AM torso on the Captain body: median %.3f mm, turned %.1f deg, moved %s' % (m, geo.ang(R), t.round(2)))
json.dump({'Mtorso_to_body': geo.M4(R, t).tolist(), 'med': m}, open('cap_torso.json', 'w'))
