import numpy as np, json, sys
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw
sys.path.insert(0,"/home/claude/kitbash/tests"); from sect import section
U="/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/"
L="/home/claude/kitbash/library/Mar Fil - Tacticus/AssaultMarines-V2/"
def stl(p):
    b=open(p,'rb').read(); n=np.frombuffer(b[80:84],np.uint32)[0]
    v=np.frombuffer(b[84:84+n*50],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]))['v'].reshape(-1,3).astype(float)
    return v, np.arange(len(v)).reshape(-1,3)
def samp(V,T,n=250000,seed=1):
    r=np.random.default_rng(seed); a,b,c=V[T[:,0]],V[T[:,1]],V[T[:,2]]; cr=np.cross(b-a,c-a); ar=np.linalg.norm(cr,axis=1)
    k=ar>0; a,b,c,cr,ar=a[k],b[k],c[k],cr[k],ar[k]
    i=r.choice(len(a),n,p=ar/ar.sum()); u,w=r.random(n),r.random(n); m=u+w>1; u[m],w[m]=1-u[m],1-w[m]
    return a[i]+u[:,None]*(b[i]-a[i])+w[:,None]*(c[i]-a[i]), cr[i]/ar[i,None], ar.sum()/2
def signed(P,S,N):
    d,j=cKDTree(S).query(P); return d*np.sign(np.einsum('ij,ij->i',P-S[j],N[j]))
F=np.array(json.load(open(L+"Legs/MarFil Assault - Legs 1.sockets.json"))['fits']['Waist']).reshape(4,4)
W=[np.array(s['matrix']).reshape(4,4) for s in json.load(open(L+"Chests/MarFil Assault - Torso 1.sockets.json"))['sockets'] if s['type']=='Waist'][0]
M=W@F; lv,lt=stl(U+"Legs/MarFil Assault - Legs 1.stl"); lv=lv@M[:3,:3].T+M[:3,3]
LS,LN,LA=samp(lv,lt)
torsos={"MarFil T1":stl(U+"Chests/MarFil Assault - Torso 1.stl")}
Z=np.load("/home/claude/work/mk8/mk8_meshes.npz"); Rz=np.array([[0,-1,0],[1,0,0],[0,0,1.]])
for nm in sys.argv[1].split(','):
    v=Z[nm+'|v'].astype(float)@Rz.T; v[:,0]-=156.9; torsos["MK8 "+nm]=(v,Z[nm+'|t'])
secs={}
for k,(V,T) in torsos.items():
    TS,TN,TA=samp(V,T)
    dl=signed(LS,TS,TN)          # legs points vs torso (neg = inside torso)
    dt=signed(TS,LS,LN)          # torso points vs legs
    pen_l=dl<-0.05; pen_t=dt<-0.05
    zb=V[:,2].min(); band=TS[:,2]<zb+1.2; gap=np.abs(dt[band])
    print(f"{k:11s} z {V[:,2].min():.2f}-{V[:,2].max():.2f} | legs inside torso: {pen_l.mean()*LA:6.2f} mm2, deepest {-dl.min():.2f} mm | torso inside legs: {pen_t.mean()*TA:6.2f} mm2, deepest {-dt.min():.2f} | bottom rim to legs: med {np.median(gap):.2f}, 90% {np.percentile(gap,90):.2f} mm")
    secs[k]=(section(V,T,0,0.0), section(V,T,1,0.6))
ls=(section(lv,lt,0,0.0),section(lv,lt,1,0.6))
# picture: x=0 side section (y-z) and y=0.6 front section (x-z) for MarFil T1 vs each MK8 asked for in argv[2]
show=["MarFil T1"]+["MK8 "+s for s in sys.argv[2].split(',')]
S=40; cols=len(show); img=Image.new("RGB",(cols*2*560,620),"white"); dr=ImageDraw.Draw(img)
for ci,k in enumerate(show):
    for vi in (0,1):
        ox=(ci*2+vi)*560; ax=(1,2) if vi==0 else (0,2); cx=ox+280; cz=420
        def P(p): return (cx+(p[ax[0]]-(1.0 if vi==0 else 0))*S, cz-(p[2]-29)*S)
        for sg in ls[vi]: dr.line([P(sg[0]),P(sg[1])],fill=(80,140,220),width=2)
        if k!="MarFil T1":
            for sg in secs["MarFil T1"][vi]: dr.line([P(sg[0]),P(sg[1])],fill=(190,190,190),width=1)
        for sg in secs[k][vi]: dr.line([P(sg[0]),P(sg[1])],fill=(220,110,40),width=2)
        dr.text((ox+10,8),f"{k}  {'side (x=0), front right' if vi==0 else 'front (y=0.6)'}",fill="black")
        for mm in range(-6,7,2): dr.line([(cx+mm*S,600),(cx+mm*S,610)],fill="black")
img.save("/home/claude/work/mk8/seat_sections.png"); print("saved")
