import bpy, sys, numpy as np
sys.path.insert(0,"/home/claude/kitbash/tests"); import rend
from PIL import Image, ImageDraw
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; rend.setup(sc,300)
Z=np.load("/home/claude/work/mk8/mk8_meshes.npz"); YC=-156.854
def ob(nm, extra=None):
    v=Z[nm+'|v'].astype(float); v=np.c_[-(v[:,1]-YC), v[:,0], v[:,2]]
    me=bpy.data.meshes.new(nm); me.from_pydata(v.tolist(),[],Z[nm+'|t'].tolist()); me.update()
    o=bpy.data.objects.new(nm,me); sc.collection.objects.link(o); return o
def stlob(p,name):
    b=open(p,'rb').read(); n=np.frombuffer(b[80:84],np.uint32)[0]
    v=np.frombuffer(b[84:84+n*50],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]))['v'].reshape(-1,3).astype(float)
    V,inv=np.unique(v,axis=0,return_inverse=True); V[:,1]-=157.177; V=np.c_[-(V[:,1]-YC),V[:,0],V[:,2]]
    me=bpy.data.meshes.new(name); me.from_pydata(V.tolist(),[],inv.reshape(-1,3).tolist()); me.update(); o=bpy.data.objects.new(name,me); sc.collection.objects.link(o); return o
rows=[]
r1=[(L,[ob(L)]) for L in "ABCDEFGHI"]; rows.append(("f",r1))
tA=ob("A"); r2=[(f"chest {n}",[tA,ob(f"Chest_equipment_{n}_L"),ob(f"Chest_equipment_{n}_R")]) for n in range(1,6)]; rows.append(("f",r2))
r3=[(f"neck {n}",[tA,ob(f"Neck_{n}")]) for n in range(1,9)]+[("STL A (collar)",[stlob("/mnt/user-data/uploads/d/new cults/Old_style_space_knight_torso/A/A.stl","stlA")])]; rows.append(("b",r3))
W=300; img=Image.new("RGB",(W*9,(W+18)*3),"white"); d=ImageDraw.Draw(img)
for ri,(view,row) in enumerate(rows):
    for ci,(lab,obs) in enumerate(row):
        dirn={"f":(0.5,1,0.35),"b":(-0.4,-1,0.6)}[view]
        f=rend.render(sc,"/home/claude/work/mk8/r",f"s{ri}_{ci}",obs,{"v":dirn},[rend.GREY]+[rend.ORANGE]*(len(obs)-1))["v"]
        img.paste(Image.open(f).convert("RGB"),(ci*W,ri*(W+18)+18)); d.text((ci*W+6,ri*(W+18)+3),lab,fill="black")
img.save("/home/claude/work/mk8/sheet.png")
