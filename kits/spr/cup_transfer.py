"""Arms whose cup the lip-ring rule missed (mostly pattern P): carry the cup from the same pose in pattern C/S
(identical forearm) by ICP of the forearm end region, in torso coordinates."""
import sys, json, re, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real')
import stlcache, fitlib as F
from scipy.spatial import cKDTree
from spr_arms import S_R, S_L
U = "/mnt/user-data/uploads/new cults/Springles/"
C = json.load(open("cups.json")); AF = json.load(open("arm_fits.json"))
def W(rel):
    a = AF[rel]; S = S_R if a["joint"] == "Shoulder R" else S_L
    return S @ np.array(a["fit"]) @ np.diag([a["scale"]] * 3 + [1])        # file coords -> torso
def key(rel):
    b = rel.split("/")[-1].replace(".stl", ""); b = re.sub(r"pattern[CPS] ", "", b)
    b = re.sub(r"^Larm melee (\d)", r"melee Larm \1", b); return b
groups = {}
for rel in AF: groups.setdefault(key(rel), []).append(rel)
out = {}
for rel in sorted(AF):
    if rel in C or "arm+hand" in rel: continue
    src = [r for r in groups[key(rel)] if r in C and "patternP" not in r] or [r for r in groups[key(rel)] if r in C]
    if not src: print("no source for", rel); continue
    s = src[0]; a, b = AF[s], AF[rel]
    Ws, Wt = W(s), W(rel)
    cupW = (S_R if a["joint"] == "Shoulder R" else S_L) @ np.array(a["fit"]) @ np.array(C[s]["M"])   # cup in torso coords
    Vs, Ts = stlcache.load(U + s); Vt, Tt = stlcache.load(U + rel)
    Ps = F.surf(Vs, Ts, 300000, 0) @ Ws[:3, :3].T + Ws[:3, 3]; Pt = F.surf(Vt, Tt, 300000, 1) @ Wt[:3, :3].T + Wt[:3, 3]
    o = cupW[:3, 3]
    src_pts = Ps[np.linalg.norm(Ps - o, axis=1) < 3.0]; tgt = Pt[np.linalg.norm(Pt - o, axis=1) < 4.5]
    R, t, d = F.icp(src_pts, cKDTree(tgt), np.eye(3), np.zeros(3), 40, 0.9)
    D = np.eye(4); D[:3, :3] = R; D[:3, 3] = t
    newW = D @ cupW
    Mt = np.linalg.inv((S_R if b["joint"] == "Shoulder R" else S_L) @ np.array(b["fit"])) @ newW
    out[rel] = dict(M=Mt.tolist(), from_=s, icp=float(np.median(d)))
    print("%-58s from %-14s icp median %.3f  moved %.2fmm %.1fdeg" % (rel[-58:], s.split('/')[0], np.median(d), np.linalg.norm(newW[:3, 3] - o), F.ang(R)))
json.dump(out, open("cups_transfer.json", "w"), indent=0)
