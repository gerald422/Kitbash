import bpy, sys, numpy as np
sys.path.insert(0,"/home/claude/kitbash/tests"); import rend
from PIL import Image, ImageDraw
names=sys.argv[sys.argv.index('--')+1].split(',')
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene; rend.setup(sc,420)
Z=np.load("/home/claude/work/mk8/mk8_meshes.npz"); Rz=np.array([[0,-1,0],[1,0,0],[0,0,1.]])
obs=[]
for nm in names:
    v=Z[nm+'|v'].astype(float)@Rz.T; v[:,0]-=156.9; t=Z[nm+'|t']
    me=bpy.data.meshes.new(nm); me.from_pydata(v.tolist(),[],t.tolist()); me.update()
    o=bpy.data.objects.new(nm,me); sc.collection.objects.link(o); obs.append(o)
tiles=[]
for o in obs:
    f=rend.render(sc,"/home/claude/work/mk8/r",o.name,[o],{"f":(0.45,1,0.35)},[rend.GREY])["f"]; tiles.append((o.name,f))
W=420; img=Image.new("RGB",(W*len(tiles),W+20),"white"); d=ImageDraw.Draw(img)
for i,(n,f) in enumerate(tiles): img.paste(Image.open(f).convert("RGB"),(i*W,20)); d.text((i*W+8,4),n,fill="black")
img.save("/home/claude/work/mk8/variants.png")
