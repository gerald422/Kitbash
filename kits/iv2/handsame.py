"""Is the hand inside each hand-held part one of the separate kit hands, in place? median distance of each kit hand's
surface to the part's surface (identity) - and, for the bolters, after ICP of the hand onto the part."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, numpy as np, os
from scipy.spatial import cKDTree
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
hands = sorted(os.listdir(geo.U + IV + "Hands-Raw")); hands = [h for h in hands if h.endswith('.stl')]
HS = {h: geo.surf(*geo.load(IV + "Hands-Raw/" + h), 4000) for h in hands}
for rel in ["Melee-Handed-Raw/223-ChainSword-A-R.stl", "Melee-Handed-Raw/226-PowerAxe-1-A-R.stl", "Melee-Handed-Raw/241-PowerSword-A-R.stl", "Melee-Handed-Raw/232-PowerHammer-1-A-R.stl",
            "Weapons-Raw/219-BoltPistol-R.stl", "Weapons-Raw/221-PlasmaPistol-R.stl", "Bolter-Individual-Raw/144-Bolter-A-4-R.stl", "Bolter-Individual-Raw/172-Bolter-A-8-R.stl", "Bolter-Individual-Raw/165-Bolter-A-7-R.stl"]:
    V, T = geo.load(IV + rel); Q = geo.surf(V, T, 200000); tree = cKDTree(Q)
    res = []
    for h, P in HS.items():
        d0 = np.median(tree.query(P)[0])
        res.append((d0, h))
    res.sort()
    print('%-42s best at identity: %s %.3f | next %s %.3f' % (rel.split('/')[-1], res[0][1], res[0][0], res[1][1], res[1][0]), flush=True)
