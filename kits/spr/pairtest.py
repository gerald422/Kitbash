import json, numpy as np, sys
from build_weapons import frame
from spr_arms import S_R, S_L
def sc(rel): return json.load(open("/home/claude/kits/out113/stage_spr/Springles/" + rel[:-4] + ".sockets.json"))
unit = lambda v: v / np.linalg.norm(v)
def arms(kind, pat, n):
    base = {"ranged": "tactical arms/pattern%s ranged %sarm %d", "heavy": "heavy weapons/pattern%s heavy %sarm %d", "duel": "2 handed melee/pattern%s duel melee %sarm %d"}[kind]
    R = f"pattern{pat} arms/" + base % (pat, "R", n) + ".stl"; L = f"pattern{pat} arms/" + base % (pat, "L", n) + ".stl"
    sr, sl = sc(R), sc(L)
    WR = S_R @ np.array(sr["fits"]["Shoulder R"]).reshape(4, 4); WL = S_L @ np.array(sl["fits"]["Shoulder L"]).reshape(4, 4)
    return WR @ np.array(sr["sockets"][0]["matrix"]).reshape(4, 4), WL @ np.array(sl["sockets"][0]["matrix"]).reshape(4, 4)
def solve(HR, HL, Fg, Fo):
    Wg = HR @ np.linalg.inv(Fg); Hh = Wg @ Fo; O = HR[:3, 3]; p = Hh[:3, 3]; q = HL[:3, 3]
    src = [unit(p - O), unit(Hh[:3, 1]), unit(HR[:3, 1])]; dst = [unit(q - O), unit(HL[:3, 1]), unit(HR[:3, 1])]
    B = sum(w * np.outer(d, a) for w, a, d in zip([4, 1, 1], src, dst)); U, _, Vt = np.linalg.svd(B); Rm = U @ np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))]) @ Vt
    return np.linalg.norm(p - q), np.linalg.norm(Rm @ (p - O) + O - q), np.degrees(np.arccos(np.clip((Rm @ Hh[:3, 1]) @ HL[:3, 1], -1, 1)))
if __name__ == "__main__":
    H = json.load(open("w/hands_all.json"))
    for rel in [a for a in sys.argv[1:] if a not in ("heavy","ranged","duel")]:
        ds = H[rel]["domes"]
        for gi in range(len(ds)):
            for oi in range(len(ds)):
                if gi == oi: continue
                Fg = frame(ds[gi]["apex"], ds[gi]["a"]); Fo = frame(ds[oi]["apex"], ds[oi]["a"])
                res = []
                for kind in (sys.argv[1] if sys.argv[1] in ("heavy","ranged","duel") else "heavy", "duel"):
                    for n in range(1, 6):
                        HR, HL = arms(kind, "C", n); b, a, ax = solve(HR, HL, Fg, Fo); res.append("%s%d %.1f/%.0f" % (kind[0], n, a, ax))
                print(rel.split("/")[-1], "grip=", np.round(ds[gi]["a"], 2), " ".join(res))
