import bpy, sys, json, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/example issues.blend")
sc = bpy.context.scene; deps = bpy.context.evaluated_depsgraph_get()
def ob(p): return next(o for o in sc.objects if o.type == 'MESH' and o.name.startswith(p))
def sock(p): return next(o for o in sc.objects if o.type == 'EMPTY' and o.name.startswith(p))
def verts(o):
    n = len(o.data.vertices); co = np.empty(n*3); o.data.vertices.foreach_get("co", co)
    M = np.array(o.matrix_world); return co.reshape(-1,3) @ M[:3,:3].T + M[:3,3]
def bvh(o):
    m = o.data; v = [o.matrix_world @ x.co for x in m.vertices]
    return BVHTree.FromPolygons(v, [p.vertices[:] for p in m.polygons])
def local(P, F): F = np.array(F); Fi = np.linalg.inv(F); return P @ Fi[:3,:3].T + Fi[:3,3]
CH, LG, BS = ob("MarFil Techmarine - Chest"), ob("MarFil Intercessor - Legs 1"), ob("base_32")
T = np.array(CH.matrix_world)
print("world up of torso Z: %.1f deg from vertical" % math.degrees(math.acos(T[2,2]/np.linalg.norm(T[:3,2]))))
# 1 base
S = sock("MarFil Intercessor - Legs 1_socket_Base").matrix_world
lv = local(verts(LG), S); bv = local(verts(BS), S)
print("BASE: lowest foot z in Base-socket frame %.2f" % lv[:,2].min())
# floor height under the feet: base verts within feet xy footprint, take a low percentile of 'top' ...
feet = lv[lv[:,2] < lv[:,2].min() + 1.5]
lo, hi = feet[:,:2].min(0), feet[:,:2].max(0)
under = bv[(bv[:,0]>lo[0])&(bv[:,0]<hi[0])&(bv[:,1]>lo[1])&(bv[:,1]<hi[1])]
print("  base z under feet: median %.2f  p90 %.2f  max %.2f" % tuple(np.percentile(under[:,2],[50,90,100])))
# per-foot: split feet by x sign
tb = bvh(BS)
Sw = S
for name, sel in (("foot A", feet[:,0] < np.median(feet[:,0])), ("foot B", feet[:,0] >= np.median(feet[:,0]))):
    f = feet[sel]; zs=[]
    for p in f[::max(1,len(f)//200)]:
        w = Sw @ Vector((p[0],p[1],p[2]+30))
        hit = tb.ray_cast(w, -Vector(Sw.col[2][:3]).normalized(), 60)
        if hit[0] is not None: zs.append((Sw.inverted() @ hit[0]).z - p[2])
    zs=np.array(zs); print("  %s: floor minus sole: median %.2f  max %.2f mm (positive = sole below the floor surface)" % (name, np.median(zs), zs.max()))
# legs vs base intersection: legs vertices inside base (ray parity)
inside=0; L = verts(LG)
for p in L[::5]:
    v=Vector(p); n=0; o=v.copy(); d=Vector((0.0123,0.0177,1)).normalized()
    for _ in range(20):
        h=tb.ray_cast(o,d,500)
        if h[0] is None: break
        n+=1; o=h[0]+d*1e-4
    inside += n%2
print("  legs vertices inside the base mesh: %d of %d sampled" % (inside, len(L[::5])))
json.dump({"ok":1}, open("/tmp/m.json","w"))
