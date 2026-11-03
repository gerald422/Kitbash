import bpy, numpy as np, pickle
bpy.ops.wm.open_mainfile(filepath='/mnt/user-data/uploads/Desktop/holster check 4A.blend')
for ob in bpy.data.objects:
    print(ob.name, ob.type, np.round(np.array(ob.matrix_world), 4).tolist(), 'delta', tuple(ob.delta_location), tuple(ob.delta_rotation_euler), 'parent', ob.parent.name if ob.parent else None)
h = bpy.data.objects['Holster']
V = np.array([v.co for v in h.data.vertices]); print('verts', len(V), 'local bbox', V.min(0).round(3), V.max(0).round(3))
W = np.array(h.matrix_world)
ref = pickle.load(open('holster_blend_ref.pkl', 'rb'))
T0 = np.eye(4); T0[:3, 3] = ref['hang']
P1 = W @ np.linalg.inv(T0) @ ref['P0']
MF = ref['MF']
Adj = np.linalg.inv(MF) @ P1 @ np.linalg.inv(ref['P0']) @ MF
print('rot euler XYZ deg (blender)', np.degrees(np.array(h.rotation_euler)).round(2), 'loc delta', (W[:3,3]-ref['hang']).round(3))
from scipy.spatial.transform import Rotation as R
print('Adj in plate frame: rotvec deg', np.degrees(R.from_matrix(Adj[:3,:3]).as_rotvec()).round(2), 'euler xyz', R.from_matrix(Adj[:3,:3]).as_euler('xyz', degrees=True).round(2), 't', Adj[:3,3].round(3))
pickle.dump({'Adj': Adj, 'W': W, 'P1': P1}, open('holster_adj.pkl', 'wb'))
