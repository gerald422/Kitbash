import sys, json, numpy as np
sys.path.insert(0, "/home/claude/tiow_blender")
import importlib, tiow_inbox as T
SP = json.load(open("/home/claude/blend/mf/icp/shin_points.json"))
L = "/home/claude/test/padlib/Mar Fil - Tacticus/Kit/Legs/"
for legs in ("29-Legs-2", "35-Legs-2-A"):
    V, Tr = T.read_stl_np(L + legs + ".stl")
    import time; t0 = time.time()
    found = T.find_shin_points(V, Tr)
    print(legs, "found", len(found), "%.1fs" % (time.time() - t0))
    for ea, eb, top, op in found:
        # nearest offline entry by top
        q = min(SP[legs], key=lambda q: np.linalg.norm(np.array(q["top"]) - top))
        a, b = np.array(q["ankle"][0]), np.array(q["ankle"][1])
        u = (eb - ea) / np.linalg.norm(eb - ea)
        print("  top diff", np.round(top - np.array(q["top"]), 3), "top", np.round(top, 3))
        print("  ankle line angle %.3f deg" % np.degrees(np.arccos(min(1, abs(u @ (b - a) / np.linalg.norm(b - a))))))
        # ball centres implied: perpendicular offsets
        mid_off = 0.5 * (ea + eb) - 0.5 * (a + b); mid_off -= u * (mid_off @ u)
        print("  midline perpendicular shift", np.round(mid_off, 3))
