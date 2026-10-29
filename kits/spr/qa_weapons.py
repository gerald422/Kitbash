"""QA sheet: every Springles weapon on a Springles arm pair on the AM torso (two-hand guns turned to meet the left
hand as the add-on does)."""
import sys, json, glob, os, numpy as np
sys.path.insert(0, '/home/claude/kits'); sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/kits/tn')
import stlcache, conv
from render_cross import am, C_MF, fit, HELM
from spr_arms import S_R, S_L
U = "/mnt/user-data/uploads/new cults/Springles/"; ST = "/home/claude/kits/out113/stage_spr/Springles/"
def sc(rel): return json.load(open(ST + rel[:-4] + ".sockets.json"))
def place(rel, S):
    s = sc(rel); j = list(s["fits"])[0]; return S @ np.array(s["fits"][j]).reshape(4, 4), s
unit = lambda v: v / np.linalg.norm(v)
def turn(Wp, s, HR, HL):
    oh = np.array(s["offHand"]).reshape(4, 4); H = Wp @ oh; O = (Wp @ np.r_[s["pivot"], 1])[:3]; p = H[:3, 3]; q = HL[:3, 3]
    src = [unit(p - O), unit(H[:3, 1]), unit(HR[:3, 1])]; dst = [unit(q - O), unit(HL[:3, 1]), unit(HR[:3, 1])]
    B = sum(w * np.outer(d, a) for w, a, d in zip([4, 1, 1], src, dst)); Uu, _, Vt = np.linalg.svd(B)
    R = Uu @ np.diag([1, 1, np.sign(np.linalg.det(Uu @ Vt))]) @ Vt
    after = np.linalg.norm(R @ (p - O) + O - q); before = np.linalg.norm(p - q)
    ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
    if ang < 0.5 or after > before - 0.05 or after > 3.0: return Wp, before
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = O - R @ O; return M @ Wp, after
PAIRS = {"gun": ("patternC arms/tactical arms/patternC ranged Rarm 3.stl", "patternC arms/tactical arms/patternC ranged Larm 3.stl"),
         "heavy": ("patternC arms/heavy weapons/patternC heavy Rarm 1.stl", "patternC arms/heavy weapons/patternC heavy Larm 1.stl"),
         "heavy_sh": ("patternC arms/tactical arms/patternC ranged Rarm 1.stl", "patternC arms/tactical arms/patternC ranged Larm 1.stl"),
         "tabar2": ("patternC arms/2 handed melee/patternC duel melee Rarm 3.stl", "patternC arms/2 handed melee/patternC duel melee Larm 3.stl"),
         "one": ("patternC arms/melee arms/patternC melee Rarm 1.stl", "patternC arms/melee arms/patternC melee Larm 1.stl")}
OR, BL = [0.95, 0.55, 0.2, 1], [0.5, 0.7, 0.95, 1]
from classify import kind
models = []; caps = []
W = sorted(r for r in (os.path.relpath(p, ST)[:-13] + ".stl" for p in glob.glob(ST + "**/*.sockets.json", recursive=True)) if sc(r)["category"] in ("Two-Handed Held", "Pistols", "Melee"))
for i, rel in enumerate(W):
    s = sc(rel); k = kind(rel)
    if s["category"] != "Two-Handed Held": pk = "one"
    elif k == "heavy": pk = "heavy_sh" if any(x in rel for x in ("las cannon.stl", "plasma cannon.stl", "rocket launcher.stl")) else "heavy"
    else: pk = k if k in PAIRS else "gun"
    Rr, Ll = PAIRS[pk]
    WR, sr = place(Rr, S_R); WL, sl = place(Ll, S_L)
    HR = WR @ np.array(sr["sockets"][0]["matrix"]).reshape(4, 4); HL = WL @ np.array(sl["sockets"][0]["matrix"]).reshape(4, 4)
    Wp = HR @ np.array(s["fits"]["Hand R"]).reshape(4, 4); gap = None
    if "offHand" in s: Wp, gap = turn(Wp, s, HR, HL)
    D = lambda k_: np.diag([k_] * 3 + [1])
    it = [[am(conv.AMT), np.eye(4).ravel().tolist(), C_MF], [stlcache.npz(U + Rr), (WR @ D(sr["scale"])).ravel().tolist(), BL], [stlcache.npz(U + Ll), (WL @ D(sl["scale"])).ravel().tolist(), BL],
          [stlcache.npz(U + rel), (Wp @ D(s["scale"])).ravel().tolist(), OR]]
    models.append(dict(name="w%03d" % i, items=it)); caps.append((rel, gap))
json.dump({"out": "/home/claude/kits/spr/rqa", "res": 220, "pad": 1.03, "models": models, "views": {"v": [0.35, 1, 0.55]}}, open("j_qa.json", "w"))
json.dump(caps, open("rqa_caps.json", "w"))
print(len(models))
