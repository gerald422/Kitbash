"""Plate canonical frame (Pc) and the plate's own mirror symmetry (Sm), stored in marfil_assault_plates.json.
Pc: the seam frame found on Legs 4A's left B plate, in the WaistPlate file (origin on the seam, Z out, Y up).
Sm: the WaistPlate registered onto itself mirrored: the right plate's mirror placement is W_R @ Sm."""
import sys, json, pickle, itertools, numpy as np
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
exec('def register_hand' + open('/home/claude/work/plates/fixmirror.py').read().split('def register_hand')[1].split('WP = ')[0])
out = pickle.load(open('/home/claude/work/plates/plates.pkl', 'rb')); mp = pickle.load(open('/home/claude/work/plates/mfplate.pkl', 'rb'))
FT = pickle.load(open('/home/claude/work/acc/fits.pkl', 'rb'))
WP = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/WaistPlate.stl'
VW, TW = load(WP); PW = samples(VW, TW, 20000)
Pc = np.linalg.inv(mp['res'][('4A', 'L')]['W']) @ out['4A']['L']['F']
med, Sm, p95 = register_hand(PW, PW, -1); print('plate onto its own mirror image: median %.3f, 95%% %.3f mm' % (med, p95))
f = '/home/claude/kitbash/kits/plates/marfil_assault_plates.json'; doc = json.load(open(f))
L = lambda M: [round(float(x), 6) for x in np.asarray(M).ravel()]
doc['plate_frame'] = {'matrix': L(Pc), 'note': 'Pc: seam frame of Legs 4A left B plate in the WaistPlate file (Z out, Y up); legs socket Plate L = W_L @ Pc'}
doc['plate_self_mirror'] = {'matrix': L(Sm), 'median_mm': round(float(med), 3), 'note': 'Sm: WaistPlate onto its own mirror image; right plate (mirror variant) placement = W_R @ Sm'}
doc['trophy_fits'] = {'CyberBrush Bug Hunters - Belt Decoration %d' % n: L(FT['trophy %d' % n]) for n in range(1, 10)}
json.dump(doc, open(f, 'w'), indent=1)
