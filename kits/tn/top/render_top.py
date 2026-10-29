import sys; sys.path.insert(0,'.'); sys.path.insert(0,'/home/claude/kits/tn')
from toprule import *
from render_cross import am, fit, HELM, C_T, C_MF, C_TN
from tn_sockets import sockets_for
import os
U="/mnt/user-data/uploads/new cults/"; TN=U+"Turtle Ninja/"
P4=TN+"TurtleNinja's Mk4 Tactical Squad/Powerpacks/"; P6=TN+"TurtleNinja's Mk2-6 Builder/Mk6/Powerpacks/"
O=[0.95,0.5,0.15,1]
TOPS=[P6+"Powerpack Banner 1.stl", P6+"Powerpack Vox Caster 1.stl", P4+"Mk4_Powerpack_Banner.stl", P4+"Mk4_Powerpack_Voxcaster.stl"]
tfit={p: np.linalg.inv(topper_frame(stlcache.load(p)[0])) for p in TOPS}
json.dump({os.path.basename(p): tfit[p].tolist() for p in TOPS}, open('topper_fits.json','w'))
tor="TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl"; S,f=sockets_for(tor); W=conv.KB@np.linalg.inv(S['Flat Waist'])
KL="/home/claude/test/kitlib/All Mar All the time/VeteranSquad/VeteranSquad/Backpacks/BackPackUpdate-1/BackPackUpdate-1/RawSTL/"
mf1=json.load(open(KL+'1.sockets.json')); mfB=np.array(mf1['fits']['Back']).reshape(4,4); mfBT=np.array(mf1['sockets'][0]['matrix']).reshape(4,4)
mf7=np.array(json.load(open(KL+'7.sockets.json'))['fits']['Back Top']).reshape(4,4)
import stlcache as sc
def L(x): return x.ravel().tolist()
models=[]
for pk in [P6+"Mk6 Powerpack 1.stl", P4+"Mk4_Powerpack_1.stl"]:
    V,T=sc.load(pk); F=pack_fit(V,T); BT=back_top(V, forward_in_file(F))
    for i,tp in enumerate(TOPS):
        base=W@S['Back']@F
        models.append(dict(name=f"{os.path.basename(pk)[:9].replace(' ','_')}_t{i}", items=[[sc.npz(TN+tor),L(W),C_T],[sc.npz(pk),L(base),C_TN],[sc.npz(tp),L(base@BT@tfit[tp]),O],[am(HELM),L(W@S['Neck']@fit(HELM,'Neck')),C_MF]]))
    # Mar Fil topper 7 on the TN pack
    models.append(dict(name=f"{os.path.basename(pk)[:9].replace(' ','_')}_mf7", items=[[sc.npz(TN+tor),L(W),C_T],[sc.npz(pk),L(W@S['Back']@F),C_TN],[sc.npz(os.path.realpath(KL+'7.stl')),L(W@S['Back']@F@BT@mf7),C_MF],[am(HELM),L(W@S['Neck']@fit(HELM,'Neck')),C_MF]]))
# TN toppers on the Mar Fil Vet pack on the AM torso
for i,tp in enumerate(TOPS):
    base=conv.S_AM['Back']@mfB
    models.append(dict(name=f"MF_t{i}", items=[[am(conv.AMT),L(np.eye(4)),C_MF],[sc.npz(os.path.realpath(KL+'1.stl')),L(base),C_MF],[sc.npz(tp),L(base@mfBT@tfit[tp]),O],[am(HELM),L(conv.S_AM['Neck']@fit(HELM,'Neck')),C_MF]]))
json.dump({"out":"/home/claude/kits/tn/top/r","res":260,"pad":1.05,"models":models,"views":{"side":[1,0,0.1],"back":[0.3,-1,0.25]}},open('j_top.json','w'))
print(len(models))
