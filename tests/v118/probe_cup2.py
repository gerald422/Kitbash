import bpy, sys, numpy as np, math
sys.path.insert(0, "/root/.config/blender/5.1/scripts/addons")
bpy.ops.wm.read_factory_settings(use_empty=True)
import tiow_inbox as T
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bmesh
def inside(tree, p, d=Vector((0.123, 0.311, 0.942)).normalized()):
    n, pos = 0, Vector(p)
    for _ in range(60):
        loc, nr, i, dd = tree.ray_cast(pos, d, 100)
        if loc is None: break
        n += 1; pos = loc + d * 1e-5
    return n % 2 == 1
bpy.ops.wm.stl_import(filepath="/home/claude/bionic/kit/LEG_HIGH.stl"); ob = bpy.context.selected_objects[0]
T.bio_clean(ob)
b = bmesh.new(); b.from_mesh(ob.data); t = BVHTree.FromBMesh(b); b.free()
c = np.array([-0.38, -0.146, 8.831])
rng = np.random.default_rng(0); D = rng.normal(size=(3000, 3)); D /= np.linalg.norm(D, axis=1)[:, None]
for r in (2.0, 2.4, 2.6, 2.8):
    ins = np.array([inside(t, c + r * d) for d in D])
    free = D[~ins]
    print(f"r {r}: free directions {len(free)} / {len(D)}; free mean dir {free.mean(0).round(2)}; solid mean dir {D[ins].mean(0).round(2) if ins.any() else None}")
# the free cone at r 2.6: angle from the opening axis covering 95 % of free dirs
op = np.array([-0.558, -0.339, 0.758])
ins = np.array([inside(t, c + 2.6 * d) for d in D])
ang = np.degrees(np.arccos(np.clip(D @ op, -1, 1)))
for a in (30, 60, 90, 120, 150, 180):
    m = ang < a
    print(f"within {a} deg of the opening axis: {100 * (~ins[m]).mean():.0f}% free")
print('--- rays from the cup centre')
def ray(d):
    loc, nr, i, dist = t.ray_cast(Vector(c), Vector(d), 20)
    return dist
for name, d in (("-opening", -op / np.linalg.norm(op)), ("-Z", (0, 0, -1)), ("+X", (1, 0, 0)), ("-X", (-1, 0, 0)), ("+Y", (0, 1, 0)), ("-Y", (0, -1, 0)), ("+X-Z", (0.7, 0, -0.7))):
    print(f"  {name:8s} first surface at {ray(np.asarray(d, float)):.3f} mm")
# best seat for a ball of r 2.689: slide the ball along +opening until no interpenetration (sampled sphere points outside the solid)
S = rng.normal(size=(1500, 3)); S /= np.linalg.norm(S, axis=1)[:, None]
opn = op / np.linalg.norm(op)
for k in np.arange(0.0, 1.6, 0.1):
    cc = c + k * opn
    n_in = sum(inside(t, cc + 2.689 * s_) for s_ in S[::3])
    print(f"  ball centre {k:.1f} mm up the opening: {n_in} of {len(S[::3])} sample points inside the thigh")
    if n_in == 0: break
