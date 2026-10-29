import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/kits/tn')
import stlcache, conv, geo, hashlib
from render_cross import am, C_MF, fit, HELM
from spr_arms import S_R, S_L
import spr_pads as SP, spr_pads2 as PA
U = SP.U; ST = SP.ST
PADS = json.load(open(SP.KL + SP.AM + "ShoulderPads/_fits.json"))["Pad R"]["m"]; F62 = np.array(PADS).reshape(4, 4)
P62 = SP.AM + "ShoulderPads/62-ShoulderPad-1.stl"; geo.load(P62); P62n = "/home/claude/kits/cache/" + hashlib.md5(P62.encode()).hexdigest() + ".npz"
OR, BL, PK = [0.95, 0.55, 0.2, 1], [0.5, 0.7, 0.95, 1], [0.85, 0.85, 0.4, 1]
def model(name, pairs, out):
    it = [[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF], [am(HELM), (conv.S_AM['Neck'] @ fit(HELM, 'Neck')).ravel().tolist(), C_MF]]
    for rel in pairs:
        s = json.load(open(ST + rel[:-4] + ".sockets.json")); side = list(s["fits"])[0][-1]
        W = (S_R if side == "R" else S_L) @ np.array(s["fits"]["Shoulder " + side]).reshape(4, 4)
        it.append([stlcache.npz(U + rel), (W @ np.diag([s["scale"]] * 3 + [1])).ravel().tolist(), OR])
        sd, Mp, Mt, h = PA.anchor(rel)
        M = Mt @ F62 if side == "R" else Mt @ SP.MX @ F62
        it.append([P62n, M.ravel().tolist(), PK])
    out.append(dict(name=name, items=it))
if __name__ == "__main__":
    out = []
    P = [("c_ranged1", ["patternC arms/tactical arms/patternC ranged Rarm 1.stl", "patternC arms/tactical arms/patternC ranged Larm 1.stl"]),
         ("c_melee3", ["patternC arms/melee arms/patternC melee Rarm 3.stl", "patternC arms/melee arms/patternC melee Larm 3.stl"]),
         ("s_heavy2", ["patternS arms/heavy weapons/patternS heavy Rarm 2.stl", "patternS arms/heavy weapons/patternS heavy Larm 2.stl"]),
         ("p_duel4", ["patternP arms/2 handed melee/patternP duel melee Rarm 4.stl", "patternP arms/2 handed melee/patternP duel melee Larm 4.stl"]),
         ("c_banner", ["patternC arms/unique/patternC banner arm.stl", "patternC arms/unique/patternC helmet hold arm.stl"]),
         ("c_slung", ["patternC arms/unique/patternC slung arm.stl", "patternC arms/unique/patternC sarge Larm.stl"])]
    for n, p in P: model(n, p, out)
    # Mar Fil 76 reference with its pad
    s76 = SP.s76; W76 = S_R @ SP.f76
    out.append(dict(name="mf76", items=[[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF], [am(SP.AM + "Arms/76-Arm-1-R-A.stl"), W76.ravel().tolist(), BL], [P62n, (SP.PAD76 @ F62).ravel().tolist(), PK]]))
    json.dump({"out": "/home/claude/kits/spr/rpad", "res": 280, "pad": 1.05, "models": out, "views": {"front": [0.2, 1, 0.15], "side": [1, 0.05, 0.1], "back": [0.2, -1, 0.3]}}, open("j_pad.json", "w"))
