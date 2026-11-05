import bpy, sys, json, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/plates"); from hol_common import stl, tf
from legs_frame import legs as legs_geo
exec(open("/home/claude/work/shin/mkblend.py").read().split("bpy.ops.wm.read_factory_settings")[0].split("U = ")[0])  # imports only
U = "/mnt/user-data/uploads/d/Kitbash Library/"
P = json.load(open("/home/claude/work/shin/pads.json")); K = {k.split("/")[-1]: k for k in json.load(open("/home/claude/work/shin/proposed.json"))}
src = open("/home/claude/work/shin/mkblend.py").read(); ns = {}
exec(src[src.index("def pad_frame"):src.index("obs = []")], {"np": np}, ns); pad_frame = ns["pad_frame"]
SET = [("Marta May 2026 - Legs 1", [("Marta May 2026 - Shin Pad 1 R", "R"), ("Marta May 2026 - Shin Pad 1 L", "L")]),
       ("Marta Jul 2026 - Legs 1", [("Marta Jul 2026 - Shin Pad 1 L", "L")]), ("Marta Jan 2026 - Legs 1", [("Marta Jan 2026 - Shin Pad 1 R", "R")])]
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/Marta shin pads - place by eye.blend")
out = {}
for i, (ln, pads) in enumerate(SET):
    _, V, T, M = legs_geo(K[ln], U); Off = np.eye(4); Off[0, 3] = 45 * i; W = Off @ M
    lo = bpy.data.objects[ln + " (locked)"]; print(ln, "legs moved: %.4f" % np.abs(np.array(lo.matrix_world) - W).max())
    for pn, s in pads:
        o = bpy.data.objects["%s - %s (place)" % (ln.replace("Marta ", ""), pn.replace("Marta ", ""))]
        PV, PT = stl(U + P[pn] + ".stl"); F = pad_frame(PV); Fi = np.linalg.inv(F); PVl = tf(Fi, PV)
        mv = np.array([v.co for v in o.data.vertices]); same = len(mv) >= 3 and np.abs(mv[:50] - PVl[:50]).max() if len(mv) == len(PVl) else None
        G = np.array(o.matrix_world); sc = np.linalg.norm(G[:3, :3], axis=0)
        Pin = np.linalg.inv(W) @ G @ Fi                       # pad file -> legs file
        out[ln + "|" + s] = {"legs": K[ln], "pad": P[pn], "padname": pn, "side": s, "pad_in_legs": Pin.tolist(), "scale": sc.tolist()}
        print("   %s %s: mesh %s, scale %s, moved %.2f mm" % (pn, s, "unchanged" if same is not None and same < 1e-4 else "CHANGED %s" % same, sc.round(3), np.linalg.norm(G[:3, 3] - np.array(json.load(open("/dev/null")) if False else G[:3, 3]))))
json.dump(out, open("/home/claude/work/shin/placed.json", "w"), indent=1)
