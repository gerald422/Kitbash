import numpy as np, json, sys
from scipy.spatial import cKDTree
U="/mnt/user-data/uploads/d/Kitbash Library/"; LIB="/home/claude/kitbash/library/"
def stl(p):
    b=open(p,'rb').read(); n=np.frombuffer(b[80:84],np.uint32)[0]
    a=np.frombuffer(b[84:84+n*50],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]))
    return a['v'].reshape(-1,3,3).astype(np.float64)
def sample(tri,n=300000,seed=0):
    r=np.random.default_rng(seed); a,b,c=tri[:,0],tri[:,1],tri[:,2]
    ar=np.linalg.norm(np.cross(b-a,c-a),axis=1); i=r.choice(len(tri),n,p=ar/ar.sum())
    u,v=r.random(n),r.random(n); m=u+v>1; u[m],v[m]=1-u[m],1-v[m]
    return a[i]+u[:,None]*(b[i]-a[i])+v[:,None]*(c[i]-a[i])
def kabsch(P,Q):
    pc,qc=P.mean(0),Q.mean(0); H=(P-pc).T@(Q-qc); U_,S,Vt=np.linalg.svd(H)
    d=np.sign(np.linalg.det(Vt.T@U_.T)); D=np.diag([1,1,d]); R=Vt.T@D@U_.T; return R,qc-R@pc
def icp(P,tree,Q,R=np.eye(3),t=np.zeros(3),it=40,trim=0.85):
    for _ in range(it):
        X=P@R.T+t; d,j=tree.query(X); k=d<=np.quantile(d,trim)
        dR,dt=kabsch(X[k],Q[j[k]]); R,t=dR@R,dR@t+dt
    d,_=tree.query(P@R.T+t); return R,t,d
def ang(R): return np.degrees(np.arccos(np.clip((np.trace(R)-1)/2,-1,1)))
mf=stl(U+"Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1.stl")
mfv=np.unique(mf.reshape(-1,3),axis=0)
sc=json.load(open(LIB+"Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1.sockets.json"))['sockets']
socks={s['type']:np.array(s['matrix']).reshape(4,4)[:3,3] for s in sc}
print("MarFil torso1 bounds", mfv.min(0).round(2), mfv.max(0).round(2))
Z=np.load("/home/claude/work/mk8/mk8_meshes.npz")
Rz=np.array([[0,-1,0],[1,0,0],[0,0,1.]])
names=sys.argv[1].split(',')
for nm in names:
    v=Z[nm+'|v'].astype(np.float64)@Rz.T; t=Z[nm+'|t']; v[:,0]-=156.9
    Q=sample(v[t]); tree=cKDTree(Q)
    # rough: match bbox centres in y, keep z
    t0=np.array([0,(mfv[:,1].min()+mfv[:,1].max())/2*0-((v[:,1].min()+v[:,1].max())/2-(mfv[:,1].min()+mfv[:,1].max())/2)*1,0])
    t0=np.array([0,(v[:,1].min()+v[:,1].max())/2-(mfv[:,1].min()+mfv[:,1].max())/2,0])
    Rg,tg,dg=icp(mfv,tree,Q,np.eye(3),t0)
    line=f"{nm:7s} bounds {v.min(0).round(1)} {v.max(0).round(1)} | global: {np.median(dg):.3f} mm med, {ang(Rg):.1f} deg, t {tg.round(2)} |"
    for j,c in socks.items():
        m=np.linalg.norm(mfv-c,axis=1)<3.0; P=mfv[m]
        d0,_=tree.query(P@Rg.T+tg)
        Rl,tl,dl=icp(P,tree,Q,Rg,tg)
        move=np.linalg.norm((c@Rl.T+tl)-(c@Rg.T+tg))
        line+=f" {j}: {np.median(d0):.2f}->{np.median(dl):.2f} ({move:.2f}mm,{ang(Rl@Rg.T):.1f}d)"
    print(line)
