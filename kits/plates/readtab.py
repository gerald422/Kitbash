import bpy, numpy as np, pickle
from scipy.spatial.transform import Rotation as R
bpy.ops.wm.open_mainfile(filepath='/mnt/user-data/uploads/Desktop/tabard check1.blend')
ref = pickle.load(open('tab_blend_ref.pkl', 'rb')); out = {}
names = [o.name for o in bpy.data.objects]; print(names)
for nm, r in ref.items():
    ob = bpy.data.objects.get(nm)
    if ob is None: print('missing', nm); continue
    W = np.array(ob.matrix_world); sc = np.linalg.norm(W[:3, :3], axis=0)
    T0 = np.eye(4); T0[:3, 3] = r['piv']; P1 = W @ np.linalg.inv(T0) @ r['P0']          # tabard file -> world (incl. his scale)
    A = r['A']                                                                           # buckle tabard socket (world, before settle)
    d0 = np.linalg.inv(A) @ r['P0']; d1 = np.linalg.inv(A) @ P1                          # pose in the socket frame, before / after
    Rr = (d1[:3, :3] / sc) @ np.linalg.inv(d0[:3, :3])
    mv = (W[:3, 3] - r['piv']); mvA = A[:3, :3].T @ mv
    print('%-32s scale %s; pivot moved %s mm in the tabard-spot frame (x across, y up, z out); turned %.1f deg (euler xyz %s)' % (nm, sc.round(3), mvA.round(2), np.degrees(R.from_matrix(Rr).magnitude()), R.from_matrix(A[:3, :3].T @ Rr @ A[:3, :3]).as_euler('xyz', degrees=True).round(1)))
    out[nm] = dict(a=r['a'], loin=r['loin'], P1=P1, M=r['M'], A=A, scale=sc)
    # check the other objects did not move
legs_moved = [n for n in names if (n.startswith('Legs') or n.startswith('Buckle'))]
pickle.dump(out, open('tab_josh.pkl', 'wb'))
