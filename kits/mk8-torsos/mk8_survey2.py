import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
U="/mnt/user-data/uploads/d/new cults/Old_style_space_knight_torso/"
def stl(p):
    b=open(p,'rb').read(); n=np.frombuffer(b[80:84],np.uint32)[0]
    return np.frombuffer(b[84:84+n*50],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]))['v'].reshape(-1,3).astype(float)
def comps(V,T):
    n=len(V); r=np.r_[T[:,0],T[:,1]]; c=np.r_[T[:,1],T[:,2]]
    return connected_components(coo_matrix((np.ones(len(r)),(r,c)),shape=(n,n)),directed=False)
v=stl(U+"A/A.stl"); V,inv_=np.unique(v,axis=0,return_inverse=True); T=inv_.reshape(-1,3)
k,lab=comps(V,T); sz=np.bincount(lab)
print("STL A components:",k,"sizes",sorted(sz)[::-1][:8])
for i in np.argsort(sz)[::-1][:6]:
    P=V[lab==i]; print("  comp",sz[i],"v x",P[:,0].min().round(1),P[:,0].max().round(1),"z",P[:,2].min().round(1),P[:,2].max().round(1))
Z=np.load("/home/claude/work/mk8/mk8_meshes.npz")
B=Z['A|v'].astype(float); kB,labB=comps(B,Z['A|t']); print("blend A components:",kB, sorted(np.bincount(labB))[::-1][:8])
# symmetry plane of blend A (raw y): mirror y about c, ICP translation in y only
tb=cKDTree(B)
for c in (-156.9,):
    M=B.copy(); M[:,1]=2*c-M[:,1]
    for _ in range(15):
        d,j=tb.query(M); k_=d<np.quantile(d,0.7); dy=np.mean(B[j[k_],1]-M[k_,1]); M[:,1]+=dy; c+=dy/2
    print("symmetry centre y = %.4f (median %.4f)"%(c,np.median(tb.query(M)[0])))
yc=c
for n in range(1,6):
    L=Z[f'Chest_equipment_{n}_L|v'].astype(float); R=Z[f'Chest_equipment_{n}_R|v'].astype(float)
    Lm=L.copy(); Lm[:,1]=2*yc-Lm[:,1]; d,_=cKDTree(R).query(Lm)
    print(f"chest {n}: R vs mirror(L) median {np.median(d):.3f} 95% {np.percentile(d,95):.3f} max {d.max():.3f}")
for a in range(1,9):
    for b in range(a+1,9):
        A_=Z[f'Neck_{a}|v']; B_=Z[f'Neck_{b}|v']
        if len(A_)==len(B_) and np.allclose(A_,B_,atol=1e-4): print(f"Neck_{a} == Neck_{b}")
for a in range(1,9):
    N=Z[f'Neck_{a}|v'].astype(float); Nm=N.copy(); Nm[:,1]=2*yc-Nm[:,1]; d,_=cKDTree(N).query(Nm); kN,_=comps(N,Z[f'Neck_{a}|t'])
    print(f"Neck_{a}: {len(N)} v, {kN} pieces, self-mirror median {np.median(d):.3f}")
