import sys; sys.path.insert(0, '/home/claude/kits')
import geo, qr, ksheet, numpy as np
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
G, O, B, P, GR = qr.GREY, qr.ORANGE, qr.BLUE, qr.PURPLE, qr.GREEN
ch = ("Chest-Raw/12-Chest-1.stl", G); lg = ("Legs-Raw/17-Legs-1.stl", G)
PI = "PlasmaIncinerator-Raw/"; PY = "Pyreblaster-Raw/"; DS = "Desolator-Raw/"
groups = {
 'dual63': [ch, lg, ("Bolter-Dual-Raw/63-Bolter-1-A.stl", O), ("BackPacks-Raw/266-BackPack-1.stl", B), ("Helmets-Heads-Raw/1-Helmet-1.stl", P)],
 'deso': [ch, lg, (DS + "205-Desolator-1.stl", O), (DS + "206-Belt-Desolator-1.stl", B), (DS + "207-Desolator-2.stl", P), (DS + "208-Belt-Desolator-2.stl", GR)],
 'deso_bits': [(DS + "213-SuperFrag-A.stl", O), (DS + "217-VengorLauncher-A.stl", B), ("Rocks-Raw/283-Rock-16.stl", P), ("Rocks-Raw/285-Rock-24.stl", GR)],
 'plasma1': [ch, lg, (PI + "179-PlasmaIncinerator-1-A.stl", O), (PI + "181-Cable-PlasmaIncinerator-1.stl", B)],
 'plasma4': [ch, lg, (PI + "188-PlasmaIncinerator-4-A-R.stl", O), (PI + "PlasmaIncinerator-Left/189-PlasmaIncinerator-4-B-L.stl", P), (PI + "190-Cable-PlasmaIncinerator-4.stl", B)],
 'plasma56': [ch, lg, (PI + "191-PlasmaIncinerator-5-R.stl", O), (PI + "192-Cable-PlasmaIncinerator-5.stl", B), (PI + "193-PlasmaIncinerator-6.stl", P), (PI + "194-Cable-PlasmaIncinerator-6.stl", GR)],
 'pyre': [ch, lg, (PY + "195-Pyreblaster-1.stl", O), (PY + "202-Pyreblaster-8.stl", P)],
 'pyre79': [ch, lg, (PY + "201-Pyreblaster-7.stl", O), (PY + "Pyreblaster-Left/201-Pyreblaster-7-L.stl", P), (PY + "203-Pyreblaster-9-A.stl", B), (PY + "204-Pyreblaster-9-B.stl", GR)],
}
rows = []
V3 = {"front": (0, -1, 0.1), "side": (1, 0, 0.05), "top": (0, 0, 1)}
for g, items in groups.items():
    for rel, _ in items: geo.load(IV + rel)
    p = qr.run(g, [(IV + r, np.eye(4), c) for r, c in items], views=V3, out="/home/claude/kits/iv2/look", res=420)
    rows.append([(p[v], f"{g} {v}") for v in V3])
ksheet.sheet(rows, "/home/claude/kits/iv2/look5.png", cell=290)
