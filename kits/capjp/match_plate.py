import numpy as np, itertools
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as R
def load(p):
    d=open(p,'rb').read(); n=int.from_bytes(d[80:84],'little')
    a=np.frombuffer(d[84:84+50*n],dtype=np.dtype([('n','<f4',3),('v','<f4',(3,3)),('a','<u2')])); return a['v'].astype(float)
def sample(T, n=6000, seed=0):
    rng=np.random.default_rng(seed); a,b,c=T[:,0],T[:,1],T[:,2]
    ar=np.linalg.norm(np.cross(b-a,c-a),axis=1); i=rng.choice(len(T),n,p=ar/ar.sum())
    u,v=rng.random(n),rng.random(n); m=u+v>1; u[m],v[m]=1-u[m],1-v[m]
    return a[i]+u[:,None]*(b[i]-a[i])+v[:,None]*(c[i]-a[i])
D='/mnt/user-data/uploads/new cults/All Mar All the time/CaptainWithJumpPack/CaptainWithJumpPack/RawStl/'
P=sample(load('/home/claude/kits/hip/WaistPlate.stl'),4000)
def icp(src, tree, Rm, t, it=40, trim=0.8):
    for _ in range(it):
        Q=src@Rm.T+t; d,j=tree.query(Q); k=d<=np.quantile(d,trim)
        A=src[k]; B=tree.data[j[k]]; ca,cb=A.mean(0),B.mean(0)
        H=(A-ca).T@(B-cb); U,S,Vt=np.linalg.svd(H); dd=np.sign(np.linalg.det(Vt.T@U.T))
        Rm=Vt.T@np.diag([1,1,dd])@U.T; t=cb-Rm@ca
    d,_=tree.query(src@Rm.T+t); return Rm,t,np.median(d),np.quantile(d,0.9)
for f in ['8-WaistPlate-1.stl','9-WaistPlate-2.stl','10-WaistPlate-3.stl']:
    Tg=sample(load(D+f),60000); tree=cKDTree(Tg)
    best=None
    rots=R.random(400,random_state=1).as_matrix()
    for Rm in rots:
        # centre source on random target points
        for c in Tg[np.random.default_rng(2).choice(len(Tg),3)]:
            t=c-Rm@P.mean(0)
            Rm2,t2,med,q9=icp(P,tree,Rm,t,it=8)
            if best is None or med<best[2]: best=(Rm2,t2,med,q9)
    Rm,t,med,q9=icp(P,tree,best[0],best[1],it=60,trim=0.9)
    print(f, 'median %.3f  q90 %.3f'%(med,q9), 'centre', (P.mean(0)@Rm.T+t).round(2))
    np.save(f[:-4]+'_fit.npy', np.vstack([np.c_[Rm,t],[0,0,0,1]]))
