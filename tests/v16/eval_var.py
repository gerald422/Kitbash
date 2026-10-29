import json, numpy as np
exec(open("/home/claude/blend/mf/icp/icp.py").read()); exec(open("/home/claude/blend/mf/icp/points.py").read())
VF = json.load(open("/home/claude/test/v16/var_frames.json")); SP = json.load(open("/home/claude/blend/mf/icp/shin_points.json"))
SPL = json.load(open("/home/claude/blend/mf/icp/shin_place.json"))
def ang(R): return np.degrees(np.arccos(np.clip((np.trace(R[:3, :3]) - 1) / 2, -1, 1)))
def padmw(pre, pad):
    Z = np.load(f"/home/claude/blend/mf/{pre}.npz"); M = json.load(open(f"/home/claude/blend/mf/{pre}.json")); return Z[M[pad]["key"] + "_mw"]
def opening(V, c, r):
    d = np.linalg.norm(V - c, axis=1); cup = V[np.abs(d - r) < 0.06]; o = c - cup.mean(0); return o / np.linalg.norm(o)
# offline rig frames
off = {}
for key, pre, knee in (("chap knee L", "chap_parts", "Knee-A-Pose.L"), ("tech knee L", "tech_parts", "Knee-L-Pose")):
    p = SP[key][0]; V, _, _ = rig("/home/claude/blend/mf/" + pre, knee)
    off[pre] = frame3("shin", p["ankle"][0], p["ankle"][1], p["top"], opening(V, np.array(p["hole"]), p["r"]))
pads = {"tech_parts": padmw("tech_parts", "Intercessor-ShinPad-L"), "chap_parts": padmw("chap_parts", "ShinPad-L-Chaplain")}
def rigdiff(St, Sc):
    Ft = np.linalg.inv(St) @ pads["tech_parts"]; Fc = np.linalg.inv(Sc) @ pads["chap_parts"]
    return ang(np.linalg.inv(Fc) @ Ft), np.linalg.norm(Ft[:3, 3] - Fc[:3, 3])
print("offline: rigs %.3f deg %.3f" % rigdiff(off["tech_parts"], off["chap_parts"]))
for var in "ABCD":
    St = np.array(VF[f"{var}|tech_parts"][0]); Sc = np.array(VF[f"{var}|chap_parts"][0])
    a, m = rigdiff(St, Sc)
    s = "%s: rigs %.3f deg %.3f | vs offline tech %.2f chap %.2f |" % (var, a, m, ang(np.linalg.inv(off["tech_parts"]) @ St), ang(np.linalg.inv(off["chap_parts"]) @ Sc))
    for legs in ("29-Legs-2", "35-Legs-2-A"):
        for S in VF[f"{var}|{legs}"]:
            S = np.array(S)
            best = min((ang(np.linalg.inv(np.array(F)) @ S), np.linalg.norm(np.array(F)[:3, 3] - S[:3, 3])) for k, F in SPL["frames"].items() if k.startswith(legs))
            s += " %.2f/%.2f" % best
    print(s)
