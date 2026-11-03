import sys, numpy as np, pickle, itertools
sys.path.insert(0, '/home/claude/work/van'); from reg import surf, register
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
exec('def register_hand' + open('/home/claude/work/plates/fixmirror.py').read().split('def register_hand')[1].split('WP = ')[0])
hs = pickle.load(open('/home/claude/work/plates/holster_socket.pkl', 'rb'))
CB = '/mnt/user-data/uploads/d/Kitbash Library/CyberBrush - Tacticus/Space Bugs Hunters/Space Bug Hunters Belt Decorations/Accessories/CyberBrush Bug Hunters - Belt Decoration %d.stl'
SH = '/mnt/user-data/uploads/d/new cults/All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL/Accesory/%s.stl'
fits = {}
# trophies: loop at the top; frame origin = loop centre, Z out = -Y (their face), Y = +Z (up)
for n in range(1, 10):
    V, T = load(CB % n); top = V[V[:, 2] > V[:, 2].max() - 1.6]; c = top.mean(0)
    F = frame(c, np.array([0, -1.0, 0]), np.array([0, 0, 1.0])); fits['trophy %d' % n] = np.linalg.inv(F)
    print('trophy %d: loop centre %s, %d pts' % (n, c.round(2), len(top)))
# sheaths: register onto the VitalyKhan holster Josh placed (no mirror)
VKs = surf(hs['hf'], 30000)
for nm in ('220-SheatPistol-6', '215-SheatPistol-1', '217-SheatPistol-3'):
    A = surf(SH % nm, 20000)
    for want in (1, -1):
        med, Mx, p95 = register_hand(A, VKs, want); print('%s -> VK holster (%s): median %.3f, 95%% %.3f mm' % (nm, 'rigid' if want > 0 else 'mirrored', med, p95))
        if want > 0: fits.setdefault('sheath_' + nm, Mx)
pickle.dump(fits, open('fits.pkl', 'wb'))
