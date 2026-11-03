import bpy, numpy as np, pickle
from scipy.spatial.transform import Rotation as R
bpy.ops.wm.open_mainfile(filepath='/mnt/user-data/uploads/Desktop/sheath check 4A.blend')
ref = pickle.load(open('sheath_blend_ref.pkl', 'rb')); mp = pickle.load(open('/home/claude/work/plates/mfplate.pkl', 'rb')); hs = pickle.load(open('/home/claude/work/plates/holster_socket.pkl', 'rb'))
for ob in bpy.data.objects: print(ob.name, np.array(ob.matrix_world)[:3, 3].round(3), 'scale', np.linalg.norm(np.array(ob.matrix_world)[:3, :3], axis=0).round(3), 'hidden', ob.hide_get())
s = bpy.data.objects['Sheath (move me)']; W = np.array(s.matrix_world); sc = np.linalg.norm(W[:3, :3], axis=0)
T0 = np.eye(4); T0[:3, 3] = ref['c']; P1 = W @ np.linalg.inv(T0) @ ref['P0']
d = np.linalg.inv(ref['P0']) @ P1; print('sheath change in its own frame: move %s mm, turn %.1f deg' % (d[:3, 3].round(2), np.degrees(R.from_matrix(d[:3, :3] / sc).magnitude())))
print('legs/plates moved:', max(np.abs(np.array(bpy.data.objects[n].matrix_world) - X).max() for n, X in (('Legs 4A', ref['M']), ('WaistPlate L', ref['M'] @ mp['res'][('4A', 'L')]['W']))).round(4))
# sheath fit relative to the plate's holster socket: sheath file -> socket frame
Sock = ref['M'] @ mp['res'][('4A', 'L')]['W'] @ hs['S_wp']
pickle.dump({'fit_on_plate_socket': np.linalg.inv(Sock) @ P1, 'P1': P1}, open('sheath_fit.pkl', 'wb')); print('saved')
