import bpy, numpy as np, pickle
from scipy.spatial.transform import Rotation as R
bpy.ops.wm.open_mainfile(filepath='/mnt/user-data/uploads/Desktop/buckle 8A.blend')
ref = pickle.load(open('buckle8a_ref.pkl', 'rb')); BS = pickle.load(open('buckle_sockets.pkl', 'rb'))
for ob in bpy.data.objects: print(ob.name, np.array(ob.matrix_world)[:3, 3].round(3), 'scale', np.linalg.norm(np.array(ob.matrix_world)[:3, :3], axis=0).round(3))
b = [o for o in bpy.data.objects if o.name.startswith('Buckle')][0]; W = np.array(b.matrix_world)
T0 = np.eye(4); T0[:3, 3] = ref['c']; P1 = W @ np.linalg.inv(T0) @ ref['P0']
L = np.array(bpy.data.objects['Legs 8A'].matrix_world); print('legs moved', np.abs(L - ref['M']).max().round(4))
d = np.linalg.inv(ref['P0']) @ P1; print('buckle change in its own frame: move %s mm, turn %.1f deg' % (d[:3, 3].round(2), np.degrees(R.from_matrix(d[:3, :3]).magnitude())))
BS['pose']['8A'] = np.linalg.inv(ref['M']) @ P1; pickle.dump(BS, open('buckle_sockets.pkl', 'wb')); print('saved 8A pose')
