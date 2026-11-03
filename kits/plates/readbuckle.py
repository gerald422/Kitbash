import bpy, numpy as np, pickle
from scipy.spatial.transform import Rotation as R
bpy.ops.wm.open_mainfile(filepath='/mnt/user-data/uploads/Desktop/buckle check.blend')
ref = pickle.load(open('buckle_blend_ref.pkl', 'rb')); NB = pickle.load(open('buckle_anchor2.pkl', 'rb'))
got = {}
for ob in bpy.data.objects:
    W = np.array(ob.matrix_world)
    if ob.name in ref:
        a, M = ref[ob.name]; A = np.linalg.inv(M) @ W; A0 = NB[a]
        sc = np.linalg.norm(W[:3, :3], axis=0)
        print('%-32s moved %.2f mm, turned %.1f deg, scale %s, parent %s' % (ob.name, np.linalg.norm((M @ A)[:3, 3] - (M @ A0)[:3, 3]), np.degrees(R.from_matrix((A[:3, :3] / sc) @ A0[:3, :3].T).magnitude()), sc.round(3), ob.parent))
        A[:3, :3] = A[:3, :3] / sc; got[a] = A
    else:
        print('%-32s loc %s' % (ob.name, W[:3, 3].round(3)))
pickle.dump(got, open('buckle_josh.pkl', 'wb'))
