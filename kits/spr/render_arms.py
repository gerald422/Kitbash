import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/kits/tn')
import stlcache
from render_cross import am, C_MF, C_TN
from spr_arms import S_R, S_L
U = "/mnt/user-data/uploads/new cults/Springles/"
AF = json.load(open("arm_fits.json"))
TOR = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/Chest/23-Torso-2.stl'
OR, BL = [0.95, 0.55, 0.2, 1], [0.45, 0.7, 0.95, 1]
def item(rel, col):
    a = AF[rel]; S = S_R if a["joint"] == "Shoulder R" else S_L
    M = S @ np.array(a["fit"]) @ np.diag([a["scale"]] * 3 + [1])
    return [stlcache.npz(U + rel), M.ravel().tolist(), col]
pairs = [("patternC arms/tactical arms/patternC ranged Rarm 1.stl", "patternC arms/tactical arms/patternC ranged Larm 1.stl"),
         ("patternC arms/melee arms/patternC melee Rarm 3.stl", "patternC arms/melee arms/patternC melee Larm 3.stl"),
         ("patternP arms/2 handed melee/patternP duel melee Rarm 4.stl", "patternP arms/2 handed melee/patternP duel melee Larm 4.stl"),
         ("patternS arms/heavy weapons/patternS heavy Rarm 2.stl", "patternS arms/heavy weapons/patternS heavy Larm 2.stl"),
         ("patternC arms/unique/patternC banner arm.stl", "patternC arms/unique/patternC helmet hold arm.stl"),
         ("patternS arms/unique/patternS sarge Rarm.stl", "patternS arms/unique/patternS sarge Larm.stl"),
         ("patternP arms/unique/patternP slung arm+hand.stl", "patternP arms/unique/patternP unsheathing Larm.stl"),
         ("patternS arms/tactical arms/patternS ranged Rarm 5.stl", "patternS arms/tactical arms/patternS ranged Larm 5.stl")]
models = []
for i, (r, l) in enumerate(pairs):
    models.append(dict(name="p%d" % i, items=[[am(TOR), np.eye(4).ravel().tolist(), C_MF], item(r, OR), item(l, BL)]))
json.dump({"out": "/home/claude/kits/spr/r", "res": 300, "pad": 1.05, "models": models,
           "views": {"front": [0, 1, 0.15], "top": [0.0, 0.2, 1], "side": [1, 0.1, 0.1]}}, open("j_arms.json", "w"))
print(len(models))
