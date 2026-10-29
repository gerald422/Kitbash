import sys; sys.path.insert(0,'.')
from toprule import *
import os
sys.path.insert(0,'/home/claude/kits/tn/top')
U="/mnt/user-data/uploads/new cults/"; TN=U+"Turtle Ninja/"
R6="TurtleNinja's Mk2-6 Builder/Mk6/Powerpacks/"; R4="TurtleNinja's Mk4 Tactical Squad/Powerpacks/"
OUT="/home/claude/kits/out112/stage_top/Turtle Ninja/"
def write(rel, d):
    p=OUT+rel[:-4]+'.sockets.json'; os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(d, open(p,'w'), indent=1); print('wrote', rel)
def rnd(M):
    U_,_,Vt=np.linalg.svd(M[:3,:3]); M=M.copy(); M[:3,:3]=U_@Vt; return np.round(M,6).ravel().tolist()
for rel in [R6+"Powerpack Banner 1.stl", R6+"Powerpack Vox Caster 1.stl", R4+"Mk4_Powerpack_Banner.stl", R4+"Mk4_Powerpack_Voxcaster.stl"]:
    V,T=stlcache.load(TN+rel); Ft=topper_frame(V)
    write(rel, dict(schemaVersion=1, part=os.path.basename(rel)[:-4], category="Backpack Toppers", sockets=[], fits={"Back Top": rnd(np.linalg.inv(Ft))},
        notes={"Back Top": "pole tip 1.1 mm into the pack top, pole up, face forward (as the Mk4 vox caster is exported on the Mk4 packs)"}))
# Powerpack 1: the Mk6 pack with a vox caster, standing up, at 0.92 scale: placed like Mk6 Powerpack 1 with the mount plates' centres together
exec(open('decomp2.py').read().split("Vv,Tv=")[0])   # gives s, R, t for Mk6 Powerpack 1 -> Powerpack 1
Vp,Tp=stlcache.load(P6+"Mk6 Powerpack 1.stl"); Fp=pack_fit(Vp,Tp)
M=merge_flats([(A,n,c) for A,n,c,o,ss in flats.flats(Vp,Tp,min_area=0.5)]); big=max([m for m in M if abs(m[1][2])>0.95], key=lambda m:m[0]); cp=big[2]
cm=s*R@cp+t
G=np.eye(4); G[:3,:3]=R.T; G[:3,3]=R.T@(cm-t)/s - R.T@cm   # merged file -> Mk6 pack file, rigid, plate centre exact
Fm=Fp@G
# its vox gets a Back Top socket too? no: the vox is part of the file. Plain backpack.
write(R6+"Powerpack 1.stl", dict(schemaVersion=1, part="Powerpack 1", category="Backpacks", sockets=[], fits={"Back": rnd(Fm)},
    notes={"Back": "Mk6 Powerpack 1 with a vox caster, exported standing at 0.92 scale: mount plate centre on the back plate like Mk6 Powerpack 1 (shape match 0.085 mm at that scale)"}))
print('scale', s)
