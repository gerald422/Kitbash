exec(open("/home/claude/test/variants/exp_rock.py").read().split("for kind in")[0])
side = "R"
byeye_shin(pB, legs29, a29[side], "marfilB", stage=0)
Aw = unit(a29[side].matrix_world); Ai = np.array(Aw.inverted())
d = Aw.to_3x3() @ Vector((0, 0, -1))
for band in (None, (Aw.translation, Aw.to_3x3() @ Vector((1, 0, 0)), 2.0)):
    keep = pB.matrix_world.copy()
    mv = T.settle_onto(pB, [legs29], d, sink=0.0, band=band)
    print("band" if band else "full", "slide", mv)
    pB.matrix_world = keep
# per-sample contact distances along d inside the band
from mathutils.bvhtree import BVHTree
pv, pt = T._world_tris(pB, deps); lv, lt = T._world_tris(legs29, deps)
Lp = pv @ Ai[:3, :3].T + Ai[:3, 3]; Ll = lv @ Ai[:3, :3].T + Ai[:3, 3]
lb = BVHTree.FromPolygons(Ll.tolist(), lt.tolist())
m = np.abs(Lp[:, 0]) < 2
hits = []
for q in Lp[m][::3]:
    h = lb.ray_cast(Vector(q), Vector((0, 0, -1)), 30)
    if h[0] is not None: hits.append((h[3], q))
hits.sort(key=lambda t: t[0])
print("closest pad->leg rays (dist, pad point in anchor frame):")
for dd, q in hits[:8]: print(f"   {dd:6.2f}  {np.round(q, 2)}")
pb = BVHTree.FromPolygons(Lp.tolist(), pt.tolist())
mh = np.abs(Ll[:, 0]) < 2
hits = []
for q in Ll[mh]:
    h = pb.ray_cast(Vector(q), Vector((0, 0, 1)), 30)
    if h[0] is not None: hits.append((h[3], q))
hits.sort(key=lambda t: t[0])
print("closest leg->pad rays:")
for dd, q in hits[:8]: print(f"   {dd:6.2f}  {np.round(q, 2)}")
