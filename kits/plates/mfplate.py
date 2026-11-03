import sys, numpy as np, pickle, json
sys.path.insert(0, '/home/claude/work/van'); from reg import surf, register
from scipy.spatial import cKDTree
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
exec(open('/home/claude/work/plates/vkplate.py').read().split('FL, PL =')[0].split('exec(open')[0])     # imports only
out = pickle.load(open('plates.pkl', 'rb'))
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'
VW, TW = load(WP); PW = samples(VW, TW, 20000)
def vk_frame(D, legs, plate):
    P = surf(D + plate + '.stl', 30000); L = surf(D + legs + '.stl', 200000); lc = L.mean(0)
    seam = P[cKDTree(L).query(P)[0] < 0.3]; c = P.mean(0); _, _, E = np.linalg.svd(P - c, full_matrices=False); nrm = E[2]
    o = c - lc; o[2] = 0
    if nrm @ o < 0: nrm = -nrm
    return frame(seam.mean(0), nrm, np.array([0, 0, 1.0]))
res = {}
for n in range(1, 9):
    a = '%dA' % n; VB, TB = load(LD % ('%dB' % n) + '.stl')
    for s in 'RL':
        Bp = samples(VB, TB[out[a][s]['sel']], 15000)
        med, Mbw, p95 = register(Bp, PW)                    # 4B plate patch -> WaistPlate file
        res[(a, s)] = dict(W=np.linalg.inv(Mbw), med=med, p95=p95, mirror=np.linalg.det(Mbw[:3, :3]) < 0)   # WaistPlate file -> legs file
        print('%s %s: WaistPlate on the B plate: median %.3f, 95%% %.3f mm %s' % (a, s, med, p95, '(mirrored copy)' if res[(a, s)]['mirror'] else ''))
# VitalyKhan hang point and the two holster poses, in VitalyKhan plate frames (model-left plates)
CH = '/home/claude/work/chap/objects/'; W = '/home/claude/work/van/'
ref = np.array([-4.33, -6.57, 19.62])                       # hang point found on the chaplain-plate (its file = model coords)
F_ch = vk_frame(CH, 'Legs', 'Hip l'); hang_vk = np.linalg.inv(F_ch) @ np.append(ref, 1)
hol = {}
for tag, D, legs, plate, h in (('back (V1/V2/V4)', W + 'v1/', 'Legs', 'Hip l', 'Holster r'), ('down (V5)', W + 'v5/', 'legs', 'hip l', 'holster l')):
    Fp = vk_frame(D, legs, plate); hol[tag] = (np.linalg.inv(Fp), D + h + '.stl')
pickle.dump(dict(res=res, hang_vk=hang_vk, hol=hol), open('mfplate.pkl', 'wb'))
print('hang point in the plate frame (x along the plate, y up, z out): %s mm' % np.round(hang_vk[:3], 2))
