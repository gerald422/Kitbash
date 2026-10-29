import sys, json, numpy as np, hashlib
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/kits/tn')
import stlcache, conv, geo
from render_cross import am, C_MF, fit, HELM
from spr_arms import S_R, S_L
U = "/mnt/user-data/uploads/new cults/Springles/"; ST = "/home/claude/kits/out113/stage_spr/Springles/"
AMP = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/'
F62 = np.array(json.load(open("/home/claude/test/kitlib/All Mar All the time/" + AMP + "ShoulderPads/_fits.json"))["Pad R"]["m"]).reshape(4, 4)
P62 = AMP + "ShoulderPads/62-ShoulderPad-1.stl"; geo.load(P62); P62n = "/home/claude/kits/cache/" + hashlib.md5(P62.encode()).hexdigest() + ".npz"
MX = np.diag([-1.0, 1, 1, 1]); OR, PK = [0.95, 0.55, 0.2, 1], [0.85, 0.85, 0.4, 1]
def items(rel):
    s = json.load(open(ST + rel[:-4] + ".sockets.json")); side = list(s["fits"])[0][-1]
    W = (S_R if side == "R" else S_L) @ np.array(s["fits"]["Shoulder " + side]).reshape(4, 4)
    pad = W @ np.array(next(x["matrix"] for x in s["sockets"] if x["type"] == "Pad " + side)).reshape(4, 4)
    M = pad @ F62 if side == "R" else pad @ MX @ F62
    return [[stlcache.npz(U + rel), (W @ np.diag([s["scale"]] * 3 + [1])).ravel().tolist(), OR], [P62n, M.ravel().tolist(), PK]]
pairs = []
for pat in "CPS":
    for kind, folder in (("duel melee", "2 handed melee"), ("heavy", "heavy weapons"), ("melee", "melee arms"), ("ranged", "tactical arms")):
        for n in range(1, 6):
            R = f"pattern{pat} arms/{folder}/pattern{pat} {kind} Rarm {n}.stl"
            L = f"pattern{pat} arms/{folder}/pattern{pat} {kind} Larm {n}.stl" if not (pat == "S" and kind == "melee") else f"pattern{pat} arms/{folder}/pattern{pat} Larm melee {n}.stl"
            pairs.append((f"{pat} {kind} {n}", R, L))
    u = f"pattern{pat} arms/unique/pattern{pat} "
    pairs += [(f"{pat} sarge", u + "sarge Rarm.stl", u + "sarge Larm.stl"), (f"{pat} unsheath", u + "unsheathing Rarm.stl", u + "unsheathing Larm.stl"),
              (f"{pat} banner/helmet", u + "banner arm.stl", u + "helmet hold arm.stl"), (f"{pat} slung+hand", u + "slung arm+hand.stl", u + "slung arm.stl")]
models = []; caps = []
for i, (nm, R, L) in enumerate(pairs):
    it = [[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF]]
    for rel in (R, L):
        try: it += items(rel)
        except FileNotFoundError: pass
    models.append(dict(name="p%03d" % i, items=it)); caps.append(nm)
json.dump({"out": "/home/claude/kits/spr/rqp2", "res": 200, "pad": 1.03, "models": models, "views": {"v": [0.3, 1, 0.35]}}, open("j_qp.json", "w")); json.dump(caps, open("rqp_caps.json", "w"))
print(len(models))
