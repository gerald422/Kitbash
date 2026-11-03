import numpy as np, json
from scipy.spatial import cKDTree
B="/mnt/user-data/uploads/d/new cults/Old_style_space_knight_torso/[BONUS]/"; M="/mnt/user-data/uploads/d/Kitbash Library/Mar Fil - Tacticus/AssaultMarines-V2/Knee Pads/"
def stl(p):
    b=open(p,'rb').read(); n=np.frombuffer(b[80:84],np.uint32)[0]
    return np.unique(np.frombuffer(b[84:84+n*50],dtype=np.dtype([('n','<3f4'),('v','<9f4'),('a','<u2')]))['v'].reshape(-1,3).astype(float),axis=0)
reg=json.load(open("/home/claude/work/mk8/shin_reg.json"))
for k,r in reg.items():
    P=stl(B+f"Shin{k}_R.stl"); Q=stl(M+f"MarFil Assault - Shin Pad {r['mf']}.stl"); T=np.array(r['T'])
    X=P@T[:3,:3].T+T[:3,3]; d1=cKDTree(Q).query(X)[0]; d2=cKDTree(X).query(Q)[0]
    print(f"Shin{k} vs MF {r['mf']}: verts {len(P)} vs {len(Q)}; new->MF med {np.median(d1):.3f} p95 {np.percentile(d1,95):.3f} max {d1.max():.3f}; MF->new p95 {np.percentile(d2,95):.3f} max {d2.max():.3f}")
