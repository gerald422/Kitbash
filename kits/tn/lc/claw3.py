import sys, json, numpy as np, os
sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/cr/dev')
import stlcache as sc, conv
from flatface import frame
np.set_printoptions(precision=3, suppress=True)
D="/mnt/user-data/uploads/new cults/Turtle Ninja/TurtleNinja's Mk4 Tactical Squad/Weapons/Single Arm/"
Vc,Tc=sc.load(D+"Mk4_Lightning_Claws.stl")
CA=np.array(json.load(open('wrist_axis.json'))['CA'])
FA=np.array(json.load(open(D+"Mk4_Lightning_Powerfist_A.sockets.json"))['fits']['Shoulder R']).reshape(4,4)
J=np.linalg.inv(FA)[:3,3]
P=Vc@CA[:3,:3].T+CA[:3,3]; c=P.mean(0); w,U=np.linalg.eigh((P-c).T@(P-c))
Y=U[:,2]; Y=Y if (J-c)@Y>0 else -Y
o=c+Y*((P-c)@Y).max()
Z=U[:,0]
Wd=(conv.S_AM['Shoulder R']@FA)[:3,:3]             # A file -> world, on the AM torso
if (Wd@Z)[2]<0: Z=-Z
Fw=frame(o,Z,Y)        # frame(origin, z, yhint): z exact, y made perpendicular
Fw=np.array(Fw)
print('socket on A\n',Fw)
fit=np.linalg.inv(Fw)@CA
def rnd(M):
    M=np.array(M); U_,_,Vt=np.linalg.svd(M[:3,:3]); M[:3,:3]=U_@Vt; return np.round(M,6).ravel().tolist()
OUT="/home/claude/kits/out112/stage_top/Turtle Ninja/TurtleNinja's Mk4 Tactical Squad/Weapons/Single Arm/"; os.makedirs(OUT,exist_ok=True)
json.dump(dict(schemaVersion=1, part="Mk4_Lightning_Powerfist_A", sockets=[dict(type="Hand R", name="Mk4_Lightning_Powerfist_A_socket_Hand R", matrix=rnd(Fw), display_type='ARROWS', display_size=3.0,
    props={'tiow_from': "where the lightning claws sit on this arm in Turtle Ninja's merged claw arm"})]), open(OUT+"Mk4_Lightning_Powerfist_A.sockets.json",'w'), indent=1)
json.dump(dict(schemaVersion=1, part="Mk4_Lightning_Claws", category="Melee", sockets=[], fits={"Hand R": rnd(fit)},
    notes={"Hand R": "over the open hand of Mk4_Lightning_Powerfist_A exactly as in Turtle Ninja's merged claw arm (shape match 0.05 mm); on other arms the cuff end sits on the wrist"}), open(OUT+"Mk4_Lightning_Claws.sockets.json",'w'), indent=1)
print('ok')
