import bpy, numpy as np, pickle
bpy.ops.wm.open_mainfile(filepath='/mnt/user-data/uploads/Desktop/buckle check.blend')
ref = pickle.load(open('buckle_blend_ref.pkl', 'rb')); NB = pickle.load(open('buckle_anchor2.pkl', 'rb'))
for en, (a, M) in ref.items():
    ln = en.replace('Buckle', 'Legs'); L = np.array(bpy.data.objects[ln].matrix_world); E = np.array(bpy.data.objects[en].matrix_world)
    print('%-8s legs moved %.3f mm / rot diff %.4f; empty world delta %s; empty delta in its own frame %s' % (a, np.linalg.norm(L[:3, 3] - M[:3, 3]), np.abs(L[:3, :3] - M[:3, :3]).max(), (E[:3, 3] - (M @ NB[a])[:3, 3]).round(3), ((np.linalg.inv(M @ NB[a]) @ E)[:3, 3]).round(3)))
