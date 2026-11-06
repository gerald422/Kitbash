import bpy, math, numpy as np
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/example issues.blend")
sc = bpy.context.scene
def o(p): return next(x for x in sc.objects if x.name.startswith(p))
T = o("MarFil Techmarine - Chest").matrix_world.to_3x3().normalized()
x, y, z = [np.array(T.col[i]) for i in range(3)]
print("torso: side axis rises %.1f deg toward +X(its right); front axis rises %.1f deg; up axis %.1f from vertical" % (math.degrees(math.asin(x[2])), math.degrees(math.asin(y[2])), math.degrees(math.acos(z[2]))))
print("torso facing (world, horizontal) %.1f deg from +Y" % math.degrees(math.atan2(-y[0], y[1])))
s = lambda n: np.array(o("MarFil Intercessor - Legs 1_socket_" + n).matrix_world.translation)
hl = s("Hip R") - s("Hip L"); pl = s("Plate R") - s("Plate L"); sh = np.array(o("MarFil Techmarine - Chest_socket_Shoulder R").matrix_world.translation) - np.array(o("MarFil Techmarine - Chest_socket_Shoulder L").matrix_world.translation)
for nm, v in (("legs hip line L->R", hl), ("legs plate line L->R", pl), ("torso shoulder line L->R", sh)):
    print("%-26s rises %+.1f deg, faces %.1f deg" % (nm, math.degrees(math.asin(v[2] / np.linalg.norm(v))), math.degrees(math.atan2(v[1], v[0]))))
B = o("MarFil Intercessor - Legs 1_socket_Base").matrix_world.to_3x3().normalized()
print("base socket up from vertical %.2f" % math.degrees(math.acos(B.col[2][2])))
# leg stance: knee/foot centroid line? use leg mesh: centroid of upper 20% vs lower 20% (lean of the legs as a whole)
L = o("MarFil Intercessor - Legs 1"); n=len(L.data.vertices); co=np.empty(n*3); L.data.vertices.foreach_get("co",co); M=np.array(L.matrix_world); P=co.reshape(-1,3)@M[:3,:3].T+M[:3,3]
zt, zb = np.percentile(P[:,2],[85,15]); top=P[P[:,2]>zt].mean(0); bot=P[P[:,2]<zb].mean(0); d=top-bot
print("legs mass lean: top vs feet  side %.1f deg, fore-aft %.1f deg" % (math.degrees(math.atan2(d[0], d[2])), math.degrees(math.atan2(d[1], d[2]))))
