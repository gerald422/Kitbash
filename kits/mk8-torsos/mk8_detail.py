import numpy as np, json
from scipy.spatial import cKDTree
Z=np.load("/home/claude/work/mk8/mk8_meshes.npz"); Rz=np.array([[0,-1,0],[1,0,0],[0,0,1.]])
def get(nm):
    v=Z[nm+'|v'].astype(float)@Rz.T; v[:,0]-=156.9; return v
L="/home/claude/kitbash/library/Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1.sockets.json"
S={s['type']:np.array(s['matrix']).reshape(4,4) for s in json.load(open(L))['sockets']}
b=S['Back'][:3,3]; n=S['Neck'][:3,3]
print("MarFil sockets: back y %.2f z %.2f | neck y %.2f z %.2f"%(b[1],b[2],n[1],n[2]))
for L_ in "ABCDEFGHI":
    v=get(L_)
    m=(np.abs(v[:,0]-b[0])<0.6)&(np.abs(v[:,2]-b[2])<0.6); by=v[m,1].min()
    m2=(np.abs(v[:,0])<0.5)&(np.abs(v[:,1]-n[1])<0.5)&(v[:,2]>31)&(v[:,2]<34); nz=np.sort(v[m2,2])[:3] if m2.any() else []
    print(f"{L_}: back face y {by:.2f} ({by-b[1]:+.2f}) | neck cradle z near socket {np.round(nz,2)}")
A=get("A"); tA=cKDTree(A)
for k in range(1,10):
    v=get(f"A.00{k}"); d,_=tA.query(v); x=v[d>0.02]
    if len(x): print(f"A.00{k}: {len(x)} new verts, x {x[:,0].min():.1f}..{x[:,0].max():.1f} y {x[:,1].min():.1f}..{x[:,1].max():.1f} z {x[:,2].min():.1f}..{x[:,2].max():.1f}")
    else: print(f"A.00{k}: same as A")
v=get("A.005"); d,_=cKDTree(get("A.001")).query(v); x=v[d>0.02]; print("A.005 vs A.001:",len(x),x.min(0).round(1) if len(x) else '', x.max(0).round(1) if len(x) else '')
v=get("A.006"); d,_=cKDTree(get("A.001")).query(v); x=v[d>0.02]; print("A.006 vs A.001:",len(x),x.min(0).round(1) if len(x) else '', x.max(0).round(1) if len(x) else '')
