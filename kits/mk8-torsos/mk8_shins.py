import numpy as np, json, itertools
from scipy.spatial import cKDTree
B="/mnt/user-data/uploads/d/new cults/Old_style_space_knight_torso/[BONUS]/"; M="/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Knee Pads/"
LIB="/home/claude/kitbash/library/Mar Fil - Tacticus/AssaultMarines-V2/Knee Pads/"
def stl(p):
    b=open(p,'rb').read(); n=np.frombuffer(b[80:84],np.uint32)[0]
    return np.unique(np.frombuffer(b[84:84+n*50],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]))['v'].reshape(-1,3).astype(float),axis=0)
def kabsch(P,Q):
    pc,qc=P.mean(0),Q.mean(0); H=(P-pc).T@(Q-qc); u,s,vt=np.linalg.svd(H); d=np.sign(np.linalg.det(vt.T@u.T)); R=vt.T@np.diag([1,1,d])@u.T; return R,qc-R@pc
def icp(P,tree,Q,R,t,it=40):
    for _ in range(it):
        X=P@R.T+t; d,j=tree.query(X); k=d<=np.quantile(d,0.85); dR,dt=kabsch(X[k],Q[j[k]]); R,t=dR@R,dR@t+dt
    return R,t,np.median(tree.query(P@R.T+t)[0])
rots=[]
for p in itertools.permutations(range(3)):
    for s in itertools.product((1,-1),repeat=3):
        R=np.zeros((3,3)); R[range(3),p]=s
        if np.linalg.det(R)>0: rots.append(R)
# L vs mirror(R)
for k in "ABC":
    L=stl(B+f"Shin{k}_L.stl"); R=stl(B+f"Shin{k}_R.stl"); Lm=L*[1,-1,1]; tr=cKDTree(R)
    Rr,tt,med=icp(Lm[::3],tr,R,np.eye(3),R.mean(0)-Lm.mean(0))
    d=tr.query(Lm@Rr.T+tt)[0]; print(f"Shin{k}: L mirrored (y) onto R: median {np.median(d):.3f} 95% {np.percentile(d,95):.3f}, rot {np.degrees(np.arccos(np.clip((np.trace(Rr)-1)/2,-1,1))):.2f} deg, t {tt.round(3)}")
mf={i:stl(M+f"MarFil Assault - Shin Pad {i}.stl") for i in range(1,9)}
res={}
for k in "ABC":
    P=stl(B+f"Shin{k}_R.stl"); best=[]
    for i,Q in mf.items():
        tr=cKDTree(Q); bi=None
        for R0 in rots:
            R,t,med=icp(P[::4],tr,Q,R0,Q.mean(0)-P.mean(0)@R0.T,it=12)
            if bi is None or med<bi[2]: bi=(R,t,med)
        R,t,med=icp(P[::2],tr,Q,bi[0],bi[1],it=40); best.append((med,i,R,t))
    best.sort(key=lambda x:x[0]); print(f"Shin{k}_R best:",[(i,round(m,3)) for m,i,_,_ in best[:4]])
    m,i,R,t=best[0]; T=np.eye(4); T[:3,:3]=R; T[:3,3]=t; res[k]={"mf":i,"median":m,"T":T.tolist()}
json.dump(res,open("/home/claude/work/mk8/shin_reg.json","w"))
