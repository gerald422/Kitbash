import bpy, sys, json, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath="/mnt/user-data/uploads/Desktop/example issues.blend")
sc = bpy.context.scene
def ob(p): return next(o for o in sc.objects if o.type == 'MESH' and o.name.startswith(p))
def sock(p): return next(o for o in sc.objects if o.type == 'EMPTY' and o.name.startswith(p))
def verts(o):
    n = len(o.data.vertices); co = np.empty(n*3); o.data.vertices.foreach_get("co", co)
    M = np.array(o.matrix_world); return co.reshape(-1,3) @ M[:3,:3].T + M[:3,3]
def bvh(o):
    v = [o.matrix_world @ x.co for x in o.data.vertices]
    return BVHTree.FromPolygons(v, [p.vertices[:] for p in o.data.polygons])
def local(P, F): F = np.array(F); Fi = np.linalg.inv(F); return P @ Fi[:3,:3].T + Fi[:3,3]
def ang(a,b): a=np.asarray(a)/np.linalg.norm(a); b=np.asarray(b)/np.linalg.norm(b); return math.degrees(math.acos(np.clip(a@b,-1,1)))
def gap(o, others, n=1500):
    P = verts(o); P = P[np.random.default_rng(0).choice(len(P), min(n,len(P)), replace=False)]
    trees=[bvh(x) for x in others]; d=[]
    for p in P:
        best=1e9
        for t in trees:
            h=t.find_nearest(Vector(p))
            if h[0] is not None: best=min(best,h[3])
        d.append(best)
    return np.array(d)
CH, LG, BS = ob("MarFil Techmarine - Chest"), ob("MarFil Intercessor - Legs 1"), ob("base_32")
T = CH.matrix_world; Ti = T.inverted()
# 2 waist: legs hip line and belt front in torso frame
H = {k: (Ti @ sock("MarFil Intercessor - Legs 1_socket_"+k).matrix_world.translation) for k in ("Hip R","Hip L","Belt Front","Belt Back","Plate R","Plate L")}
hl = H["Hip L"] - H["Hip R"]; pl = H["Plate L"] - H["Plate R"]
fb = H["Belt Front"] - H["Belt Back"]
print("WAIST (torso frame, X = torso's side axis, Y fwd, Z up)")
print("  hip line R->L  turn about Z %.1f deg, roll (one hip higher) %.1f deg" % (math.degrees(math.atan2(hl.y, hl.x)), math.degrees(math.atan2(hl.z, math.hypot(hl.x,hl.y)))))
print("  plate line R->L turn %.1f, roll %.1f" % (math.degrees(math.atan2(pl.y, pl.x)), math.degrees(math.atan2(pl.z, math.hypot(pl.x,pl.y)))))
print("  belt back->front: turn from torso fwd %.1f deg, pitch %.1f" % (math.degrees(math.atan2(-fb.x, fb.y)), math.degrees(math.atan2(fb.z, math.hypot(fb.x,fb.y)))))
# torso forward check: where the torso's own front is (Neck/Back sockets)
nk = Ti @ sock("MarFil Techmarine - Chest_socket_Neck").matrix_world.translation; bk = Ti @ sock("MarFil Techmarine - Chest_socket_Back").matrix_world.translation
print("  torso neck", np.round(nk,2), "back", np.round(bk,2))
# 3 backpack centring in torso frame
BP = ob("BBoosty Medusas Mortals - Backpack")
tv = local(verts(CH), T); pv = local(verts(BP), T)
print("PACK: torso x range %.2f..%.2f (mid %.2f), torso back socket x %.2f" % (tv[:,0].min(), tv[:,0].max(), (tv[:,0].min()+tv[:,0].max())/2, bk.x))
print("  pack x range %.2f..%.2f (mid %.2f); pack centroid x %.2f; pack z %.1f..%.1f (torso z %.1f..%.1f)" % (pv[:,0].min(), pv[:,0].max(), (pv[:,0].min()+pv[:,0].max())/2, pv[:,0].mean(), pv[:,2].min(), pv[:,2].max(), tv[:,2].min(), tv[:,2].max()))
# the pack's mount face: pack verts nearest the torso back
d = gap(BP, [CH], 3000)
P = verts(BP); 
print("  pack min gap to torso %.2f mm" % d.min())
# 4 pads: fitted sphere centre vs arm shoulder
def sphere(P):
    A = np.c_[2*P, np.ones(len(P))]; b=(P**2).sum(1); c,*_ = np.linalg.lstsq(A,b,rcond=None); return c[:3], math.sqrt(c[3]+c[:3]@c[:3])
for pad, arm, sh in (("BBoosty Medusas Mortals - Shoulder Pad Studs","MarFil Assault - Arm 7B R","MarFil Techmarine - Chest_socket_Shoulder R"),("BBoosty Medusas Mortals - Shoulder Pad Bolts","MarFil Intercessor - Arm 1 L","MarFil Techmarine - Chest_socket_Shoulder L")):
    PP = verts(ob(pad)); c, r = sphere(PP); cen = PP.mean(0)
    shp = np.array(sock(sh).matrix_world.translation)
    print("PAD %s: dome centre %.1f mm from the shoulder joint (r %.1f); pad centroid %.1f mm from it; concave side faces the shoulder? %s" % (pad[-12:], np.linalg.norm(c-shp), r, np.linalg.norm(cen-shp), (c-cen)@(shp-cen) > 0))
    pl = local(PP, T); print("    pad in torso frame z %.1f..%.1f, centroid %s" % (pl[:,2].min(), pl[:,2].max(), np.round(pl.mean(0),1)))
    dd = gap(ob(pad), [ob(arm), CH], 1500); print("    nearest gap to arm/torso: min %.2f, median %.2f" % (dd.min(), np.median(dd)))
# 5 loincloth
LC = ob("Marta Jul 2026 - Loincloth 5"); BK = ob("MarFil Assault - Buckle")
d = gap(LC, [LG, BK], 2000)
lv = local(verts(LC), sock("MarFil Intercessor - Legs 1_socket_Belt Front").matrix_world)
print("LOIN: min gap to legs/buckle %.2f mm (p5 %.2f); in Belt Front frame: x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (d.min(), np.percentile(d,5), lv[:,0].min(), lv[:,0].max(), lv[:,1].min(), lv[:,1].max(), lv[:,2].min(), lv[:,2].max()))
bf = sock("MarFil Intercessor - Legs 1_socket_Belt Front").matrix_world; bkl = local(verts(BK), bf)
print("   buckle in Belt Front frame: x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (bkl[:,0].min(), bkl[:,0].max(), bkl[:,1].min(), bkl[:,1].max(), bkl[:,2].min(), bkl[:,2].max()))
print("   belt front socket axes in torso frame: X", np.round((Ti.to_3x3() @ bf.to_3x3()).col[0],2), "Y", np.round((Ti.to_3x3() @ bf.to_3x3()).col[1],2), "Z", np.round((Ti.to_3x3() @ bf.to_3x3()).col[2],2))
# 6 TN accessory on Belt Back
TN = ob("TN Mk10 Assault - Jump Pack")
d = gap(TN, [LG], 2000)
bb = sock("MarFil Intercessor - Legs 1_socket_Belt Back").matrix_world
tl = local(verts(TN), bb)
print("BACKBIT: min gap to legs %.2f; in Belt Back frame x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (d.min(), tl[:,0].min(), tl[:,0].max(), tl[:,1].min(), tl[:,1].max(), tl[:,2].min(), tl[:,2].max()))
print("   belt back socket axes in torso frame: Y", np.round((Ti.to_3x3() @ bb.to_3x3()).col[1],2), "Z", np.round((Ti.to_3x3() @ bb.to_3x3()).col[2],2))
