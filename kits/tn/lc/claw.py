import sys, json, numpy as np
sys.path.insert(0,'/home/claude/tiow_blender'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits')
import tiow_inbox as TI
np.set_printoptions(precision=3, suppress=True)
D="/mnt/user-data/uploads/new cults/Turtle Ninja/TurtleNinja's Mk4 Tactical Squad/Weapons/Single Arm/"
z=np.load(open("npzpath.txt").read().strip()); Va,Ta=z["V"].astype(float),z["T"]
FA=np.array(json.load(open(D+"Mk4_Lightning_Powerfist_A.sockets.json"))['fits']['Shoulder R']).reshape(4,4)
J=np.linalg.inv(FA)[:3,3]; print('joint in A file', J)
W=TI.arm_wrist_frame(Va,Ta,J,'R'); print('wrist\n', W)
if W is None:
    W=TI.arm_wrist_frame(Va,Ta,J,'R',round_tol=0.2); print('wrist tol 0.2\n', W)
AM=np.array(json.load(open('A_in_merged.json'))); CM=np.array(json.load(open('claw_in_merged.json')))
CA=np.linalg.inv(AM)@CM
fit=np.linalg.inv(W)@CA
print('claw fit (Hand R)\n', fit)
json.dump(dict(W=W.tolist(), fit=fit.tolist()), open('claw_fit.json','w'))
