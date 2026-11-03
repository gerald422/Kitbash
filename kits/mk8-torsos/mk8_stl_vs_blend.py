import numpy as np, sys
from scipy.spatial import cKDTree
sys.path.insert(0,"/home/claude/kitbash/kits/mk8-torsos")
U="/mnt/user-data/uploads/d/new cults/Old_style_space_knight_torso/"
def stl(p):
    b=open(p,'rb').read(); n=np.frombuffer(b[80:84],np.uint32)[0]
    return np.frombuffer(b[84:84+n*50],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]))['v'].reshape(-1,3).astype(float)
def kabsch(P,Q):
    pc,qc=P.mean(0),Q.mean(0); H=(P-pc).T@(Q-qc); u,s,vt=np.linalg.svd(H); d=np.sign(np.linalg.det(vt.T@u.T))
    R=vt.T@np.diag([1,1,d])@u.T; return R,qc-R@pc
Z=np.load("/home/claude/work/mk8/mk8_meshes.npz")
for f,nm in (("A/A.stl","A"),("A/A.005.stl","A.005"),("D/D.stl","D")):
    S=np.unique(stl(U+f),axis=0); B=Z[nm+'|v'].astype(float); tb=cKDTree(B)
    t=np.array([0,(B[:,1].min()+B[:,1].max())/2-(S[:,1].min()+S[:,1].max())/2,B[:,2].min()-S[:,2].min()]); R=np.eye(3)
    for _ in range(30):
        X=S@R.T+t; d,j=tb.query(X); k=d<np.quantile(d,0.7); dR,dt=kabsch(X[k],B[j[k]]); R,t=dR@R,dR@t+dt
    X=S@R.T+t; d,_=tb.query(X); far=X[d>0.05]
    d2,_=cKDTree(X).query(B); farB=B[d2>0.05]
    print(f"{nm}: STL {len(S)} v, t {t.round(3)}, rot {np.degrees(np.arccos(np.clip((np.trace(R)-1)/2,-1,1))):.3f} deg, med {np.median(d):.4f}; STL-only {len(far)} v",
          f"z {far[:,2].min():.1f}-{far[:,2].max():.1f} x {far[:,0].min():.1f}-{far[:,0].max():.1f}" if len(far) else "",
          f"| blend-only {len(farB)} v", f"z {farB[:,2].min():.1f}-{farB[:,2].max():.1f}" if len(farB) else "")
