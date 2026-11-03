import numpy as np, pickle, json
exec(open('/home/claude/work/plates/plates.py').read().split('out = {}')[0])
FB = pickle.load(open('buckle_final.pkl', 'rb')); BP = pickle.load(open('buckle_part_fit.pkl', 'rb'))
V, T = load('/mnt/user-data/uploads/Desktop/buckle.stl')
# buckle pose on each legs (buckle file -> legs file): shape match where it fits, else copied from Standing 2 through the buckle spot
pose = {}
for a, r in BP.items():
    pose[a] = r['M'] if r['med'] < 0.05 else FB[a] @ np.linalg.inv(FB['S2']) @ BP['S2']['M']
    print(a, 'shape match' if r['med'] < 0.05 else 'placed at the buckle spot (different sculpted buckle)')
# sockets on the buckle (buckle file coords): Ornament = the approved buckle spot (face of the boss); Tabard = same frame, back-bottom of the buckle
ORN = np.linalg.inv(BP['S2']['M']) @ FB['S2']
L = (V - ORN[:3, 3]) @ ORN[:3, :3]                      # buckle verts in the ornament frame (x across, y up, z out)
print('buckle in the ornament frame: x %.2f..%.2f, y %.2f..%.2f, z %.2f..%.2f' % (L[:, 0].min(), L[:, 0].max(), L[:, 1].min(), L[:, 1].max(), L[:, 2].min(), L[:, 2].max()))
xc = (L[:, 0].min() + L[:, 0].max()) / 2
TAB = ORN @ np.array([[1, 0, 0, xc], [0, 1, 0, L[:, 1].min() + 0.6], [0, 0, 1, L[:, 2].min() + 0.3], [0, 0, 0, 1.0]])
pickle.dump(dict(pose=pose, ORN=ORN, TAB=TAB), open('buckle_sockets.pkl', 'wb'))
