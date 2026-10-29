import numpy as np, json, glob, os, sys
sys.path.insert(0, os.path.dirname(__file__)); from settle_lib import settle
L = "/mnt/user-data/uploads/d/Kitbash Library/"
def load(p):
    d = open(p, 'rb').read(); n = int.from_bytes(d[80:84], 'little')
    a = np.frombuffer(d[84:84 + 50 * n], dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    return a['v'].astype(float)
def M(a): return np.array(a, float).reshape(4, 4)
def xf(T, A): return A @ T[:3, :3].T + T[:3, 3]
legs = ["Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 1A", "Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 6A",
        "Mar Fil - Tacticus/Intercessors-V2/Intercessors-Bits/Legs/MarFil Intercessor - Legs 10", "Marta PunkGirl - Tacticus/51 May 2026/legs-chin pads and base/Legs/Marta May 2026 - Legs 1"]
bases = sorted(glob.glob(L + "Bases/*.stl"))
for lg in legs:
    sc = json.load(open(L + lg + ".sockets.json"))
    S = M([s for s in sc["sockets"] if s["type"] == "Base"][0]["matrix"])
    up = sc.get("upright")
    T = load(L + lg + ".stl")
    Tl = xf(np.linalg.inv(S), T.reshape(-1, 3)).reshape(-1, 3, 3)
    print(os.path.basename(lg), "lowest legs z in socket frame %.2f" % Tl[:, :, 2].min())
    for b in bases:
        bs = json.load(open(b[:-4] + ".sockets.json"))
        f = bs.get("fits", {}).get("Base")
        if f is None: print("   ", os.path.basename(b), "no Base fit"); continue
        Tb = xf(M(f), load(b).reshape(-1, 3)).reshape(-1, 3, 3)
        g = settle(Tl, Tb)
        print("    %-42s top max %.2f  gap %s" % (os.path.basename(b)[:42], Tb[:, :, 2].max(), "None" if g is None else "%.2f" % g))
