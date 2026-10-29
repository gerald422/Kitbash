"""Find a by-eye pose for pad 56 on arm 111 R: try a few, render each."""
import bpy, json, math, os, sys, tempfile
import numpy as np
from mathutils import Matrix, Vector
exec(open("/home/claude/test/diag/pad_diag.py").read().split("# the pad with the stand-in used by the test")[0])
sys.path.insert(0, "/home/claude/test/diag"); 
from mathutils.bvhtree import BVHTree
for root, ds, fs in os.walk(LIB):
    for f in fs:
        if f == "_fits.json": os.remove(os.path.join(root, f))
select(torso)
p = send(f"{MF}/Kit/Shoulder Pads/56-ShoulderPad-1.stl", "Shoulder Pads", (260, 0, 0))
sw = padA.get("tiow_swing")
loc, rot, _ = shR.matrix_world.decompose()
F = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1))) @ Matrix.Rotation(math.radians(sw), 4, 'X')
cup = Vector((0.0, 0.54, 0.34))
armtree = BVHTree.FromObject(arm, deps)   # arm local
ai = arm.matrix_world.inverted()
def top_at(xf, yf):
    o = F @ Vector((xf, yf, 20)); d = F.to_3x3() @ Vector((0, 0, -1))
    hit = armtree.ray_cast(ai @ o, (ai.to_3x3() @ d).normalized())
    return None if hit[0] is None else (F.inverted() @ (arm.matrix_world @ hit[0])).z
out = []
for cx in [float(v) for v in sys.argv[sys.argv.index("--") + 1:]][0::2] if "--" in sys.argv else (1.0, 1.75, 2.5):
  for flare in ((0.0, 15.0) if "--" not in sys.argv else [float(v) for v in sys.argv[sys.argv.index("--") + 1:]][1::2][:1]):
    # pad upright: pad X -> -F.Y, pad Y -> F.X (out), pad Z -> F.Z ; then flare about F.Y (top leans in)
    Rp = Matrix(((0, 1, 0), (-1, 0, 0), (0, 0, 1)))                 # rows: F x = pad y ; F y = -pad x ; F z = pad z
    Rf = Matrix.Rotation(math.radians(-flare), 3, 'Y')
    Rl = Rf @ Rp
    # cup ceiling (cup + 2.8 along the pad's own up) sits on the arm top under it
    ceil_local = cup + Vector((0, 0, 2.8))
    c_xy = Rl @ ceil_local
    zt = top_at(cx, 0.0)
    t = Vector((cx, 0.0, zt + 0.0)) - Rl @ ceil_local
    M_F = Matrix.Translation(t) @ Rl.to_4x4()
    p.matrix_world = F @ M_F
    tag = f"cx{cx:.2f}_f{int(flare)}"
    pv, pt = T._world_tris(p, deps); Fi = np.array(F.inverted()); Lp = pv @ Fi[:3, :3].T + Fi[:3, 3]
    La = av @ Fi[:3, :3].T + Fi[:3, 3]; Ltt = tv @ Fi[:3, :3].T + Fi[:3, 3]
    np.savez(f"/home/claude/test/diag/si_{tag}.npz", arm_v=La, arm_t=at, torso_v=Ltt, torso_t=tt, pad_v=Lp, pad_t=pt, padA=np.eye(4))
    print(tag, "pad z", Lp[:, 2].min().round(2), Lp[:, 2].max().round(2), "x", Lp[:, 0].min().round(2), Lp[:, 0].max().round(2))
    rend.render(scene, "/home/claude/test/diag", f"si_{tag}", [torso, arm, p], {"front": (0, 1, 0.15), "top": (0.3, 0.5, 1)}, [rend.GREY, rend.BLUE, rend.ORANGE], frame=F, up=(0, 0, 1))
    json.dump({"F_pad": [list(r) for r in M_F]}, open(f"/home/claude/test/diag/si_{tag}.json", "w"))
