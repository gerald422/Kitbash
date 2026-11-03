import numpy as np, json
Z=np.load("/home/claude/work/mk8/mk8_meshes.npz"); Rz=np.array([[0,-1,0],[1,0,0],[0,0,1.]])
U="/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1.stl"
def samp(V,T,n=400000):
    r=np.random.default_rng(2); a,b,c=V[T[:,0]],V[T[:,1]],V[T[:,2]]; ar=np.linalg.norm(np.cross(b-a,c-a),axis=1)
    i=r.choice(len(a),n,p=ar/ar.sum()); u,w=r.random(n),r.random(n); m=u+w>1; u[m],w[m]=1-u[m],1-w[m]
    return a[i]+u[:,None]*(b[i]-a[i])+w[:,None]*(c[i]-a[i])
bb=open(U,'rb').read(); n=np.frombuffer(bb[80:84],np.uint32)[0]
mv=np.frombuffer(bb[84:84+n*50],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]))['v'].reshape(-1,3).astype(float)
def prof(P,label):
    out=[]
    for z in (31.5,32.5,33.34,34.5,35.5):
        m=(np.abs(P[:,0])<0.4)&(np.abs(P[:,2]-z)<0.15)&(P[:,1]<0); out.append(f"z{z}:{P[m,1].min():.2f}" if m.any() else f"z{z}:-")
    print(f"{label:9s} back y at x=0 ->", " ".join(out))
prof(samp(mv,np.arange(len(mv)).reshape(-1,3)),"MarFil T1")
for L_ in "ABCDEFGHI":
    v=Z[L_+'|v'].astype(float)@Rz.T; v[:,0]-=156.9; prof(samp(v,Z[L_+'|t']),"MK8 "+L_)
