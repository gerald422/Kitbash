import sys, json, numpy as np
sys.path.insert(0, "/home/claude/blend/forclaude")
from stl_io import read_stl
from addon_ns import ns
U = "/mnt/user-data/uploads/new cults/Springles/"
AF = json.load(open("arm_fits.json"))
ok = 0; res = {}
for rel, a in sorted(AF.items()):
    v, n, t = read_stl(U + rel); V = np.asarray(v, float) * a["scale"]; T = np.asarray(t)
    F = np.array(a["fit"]); joint = np.linalg.inv(F)[:3, 3]
    side = a["joint"][-1]
    M = None
    for tol in (0.12, 0.2):
        M = ns["arm_wrist_frame"](V, T, joint, side, tol)
        if M is not None: break
    res[rel] = None if M is None else dict(M=M.tolist(), tol=tol)
    if M is not None: ok += 1
    print("%-60s %s %s" % (rel[-60:], side, "none" if M is None else "o %s y %s tol %.2f" % (M[:3, 3].round(2), M[:3, 1].round(2), tol)), flush=True)
print(ok, len(AF))
json.dump(res, open("wrists.json", "w"), indent=0)
