import sys, json, numpy as np, os
sys.path.insert(0, '/home/claude/kits/cr'); import stlcache
U = "/mnt/user-data/uploads/new cults/Springles/"
F = ["umbra bolters/bolter/umbra bolter.stl", "umbra bolters/bolter/umbra bolter 1 hand grip.stl", "umbra bolters/bolter/umbra bolter 1 hand foregrip.stl",
     "umbra bolters/bolter/umbra bolter no hands.stl", "umbra bolters/bolter/umbra bolter plastic pose 1.stl", "umbra bolters/bolter/umbra bolter plastic pose 3.stl",
     "umbra bolters/bolter/umbra bolter off trigger.stl", "umbra bolters/bolter/umbra bolter slung.stl", "umbra bolters/bolter/umbra bolter plastic 1 hand grip.stl",
     "special weapons/plasma pistol/plasma pistol.stl", "carsoran power axes/carsoran power axe A/carsoran power axe A v1.stl",
     "heavy weapons/las cannon/las cannon.stl", "heavy weapons/las cannon/las cannon grip.stl", "heavy weapons/backpacks/hw las cannon backpack.stl"]
models = [dict(name="w%02d" % i, items=[[stlcache.npz(U + f), np.eye(4).ravel().tolist(), [0.9, 0.7, 0.4, 1]]]) for i, f in enumerate(F)]
json.dump({"out": "/home/claude/kits/spr/rw", "res": 260, "pad": 1.05, "models": models,
           "views": {"py": [0, 1, 0.2], "pz": [0.05, 0.1, 1], "px": [1, 0.15, 0.2]}}, open("j_w.json", "w"))
json.dump(F, open("rw_files.json", "w"))
for f in F:
    V, T = stlcache.load(U + f); print("%-55s bbox %s %s" % (f[-55:], V.min(0).round(1), V.max(0).round(1)))
