import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
O, B = qr.ORANGE, (0.45, 0.65, 0.88, 0.6)
groups = {
 'bolt_nohand_vs_hand': [("Weapons-NoHand-Raw/255-Bolter-A-NoHand.stl", O), ("Hands-Raw/274-Hand-2-R.stl", B)],
 'pistol_nohand_vs_handed': [("Weapons-NoHand-Raw/262-BoltPistol-NoHand.stl", O), ("Weapons-Raw/219-BoltPistol-R.stl", B)],
 'sword_nohand_vs_handed': [("Melee-NoHand/246-ChainSword-NoHand.stl", O), ("Melee-Handed-Raw/223-ChainSword-A-R.stl", B)],
 'indiv172': [("Bolter-Individual-Raw/172-Bolter-A-8-R.stl", O), ("Hands-Raw/274-Hand-2-R.stl", B)],
 'indiv144': [("Bolter-Individual-Raw/144-Bolter-A-4-R.stl", O), ("Hands-Raw/274-Hand-2-R.stl", B)],
 'indiv125': [("Bolter-Individual-Raw/125-Bolter-A-1-R.stl", O), ("Arms-Raw/57-Arm-1-R.stl", B)],
 'indiv131': [("Bolter-Individual-Raw/131-Bolter-A-2-Individual-R.stl", O), ("Arms-Raw/57-Arm-1-R.stl", B)],
 'hands123': [("Hands-Raw/273-Hand-1-R.stl", O), ("Hands-Raw/275-Hand-3-R.stl", B)],
}
rows = []
V3 = {"front": (0, -1, 0), "side": (1, 0, 0), "top": (0, 0, 1)}
for g, items in groups.items():
    for rel, _ in items: geo.load(IV + rel)
    p = qr.run(g, [(IV + r, np.eye(4), c) for r, c in items], views=V3, out="/home/claude/kits/iv2/look", res=420)
    rows.append([(p[v], f"{g} {v}") for v in V3])
ksheet.sheet(rows, "/home/claude/kits/iv2/look1.png", cell=300)
