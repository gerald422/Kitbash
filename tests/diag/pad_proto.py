"""Prototype: push the pauldron on along the cavity axis (down and in) instead of straight down."""
import bpy, json, math, os, sys, tempfile
import numpy as np
from mathutils import Matrix, Vector
exec(open("/home/claude/test/diag/pad_diag.py").read().split("# the pad with the stand-in used by the test")[0])
for root, ds, fs in os.walk(LIB):
    for f in fs:
        if f == "_fits.json": os.remove(os.path.join(root, f))
select(torso)
p = send(f"{MF}/Kit/Shoulder Pads/56-ShoulderPad-1.stl", "Shoulder Pads", (260, 0, 0))
cup = Vector((0.0, 0.55, 0.33))
F = padA.matrix_world.to_3x3().normalized()
R3 = Matrix((-(F @ Vector((0, 1, 0))), F @ Vector((1, 0, 0)), F @ Vector((0, 0, 1)))).transposed()
res = {}
for tilt in [float(a) for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else (0, 30, 45, 60):
    p.matrix_world = Matrix.Translation(shR.matrix_world.translation - R3 @ cup) @ R3.to_4x4()
    d = F @ Vector((-math.sin(math.radians(tilt)), 0, -math.cos(math.radians(tilt))))
    mv = T.settle_onto(p, [arm], d, sink=0.1)
    pv, pt = T._world_tris(p, deps); Lp = pv @ Si[:3, :3].T + Si[:3, 3]
    # how far into the torso does it go?
    tb = __import__("mathutils").bvhtree.BVHTree.FromPolygons(tv.tolist(), tt.tolist())
    inside = 0
    for q in pv[::25]:
        h = tb.find_nearest(Vector(q))
        if h[0] is not None and (Vector(q) - h[0]).dot(h[1]) < -0.05: inside += 1
    print(f"tilt {tilt:4.0f}: moved {mv:6.2f}  pad z {Lp[:,2].min():5.2f}..{Lp[:,2].max():5.2f}  x {Lp[:,0].min():5.2f}..{Lp[:,0].max():5.2f}  pad pts inside torso {inside}/{len(pv[::25])}")
    np.savez(f"/home/claude/test/diag/proto_{int(tilt)}.npz", arm_v=L, arm_t=at, torso_v=Lt, torso_t=tt, pad_v=Lp, pad_t=pt, padA=np.array(inv @ padA.matrix_world))
