import sys, json, numpy as np
sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/cr/dev')
import stlcache as sc, flats
from topface import merge_flats
from scipy.spatial import cKDTree
np.set_printoptions(precision=3, suppress=True)
D="/mnt/user-data/uploads/new cults/Turtle Ninja/TurtleNinja's Mk4 Tactical Squad/Weapons/Single Arm/"
Va,Ta=sc.load(D+"Mk4_Lightning_Powerfist_A.stl"); Vc,Tc=sc.load(D+"Mk4_Lightning_Claws.stl")
AM=np.array(json.load(open('A_in_merged.json'))); CM=np.array(json.load(open('claw_in_merged.json'))); CA=np.linalg.inv(AM)@CM
P=Vc@CA[:3,:3].T+CA[:3,3]
tree=cKDTree(Va); d,_=tree.query(P); print('claw pts within 0.3 of arm:', (d<0.3).sum(), 'of', len(P))
Mc=merge_flats([(a,n,c) for a,n,c,o,s in flats.flats(Vc,Tc,min_area=1.0)])
for a,n,c in sorted(Mc,key=lambda m:-m[0])[:8]:
    cA=CA[:3,:3]@c+CA[:3,3]; nA=CA[:3,:3]@n; dd,_=tree.query(cA)
    print('claw flat A %.1f nA %s cA %s dist to arm %.2f'%(a,nA,cA,dd))
Ma=merge_flats([(a,n,c) for a,n,c,o,s in flats.flats(Va,Ta,min_area=1.0)])
J=np.array([-0.395,13.632,12.109])
print('arm flats far from joint:')
for a,n,c in sorted(Ma,key=lambda m:-np.linalg.norm(m[2]-J))[:8]: print('   A %.1f n %s c %s dist %.1f'%(a,n,c,np.linalg.norm(c-J)))
# wrist axis from the claw's long axis; origin at the arm's far end on that axis
Pc=P-P.mean(0); w,U=np.linalg.eigh(Pc.T@Pc); ax=U[:,-1]
ov=P[d<0.3].mean(0)
if (ov-P.mean(0))@ax<0: ax=-ax          # ax: from the claw toward the arm = Y into the arm
L=Va-ov; along=L@ax; lat=np.linalg.norm(L-along[:,None]*ax,axis=1)
near=Va[(lat<2.0)]
tipd=(near-ov)@ax; o=ov+ax*tipd.min()
print('axis', ax, 'overlap centre', ov, 'origin', o, 'claw extent along -ax', ((P-o)@ax).min())
json.dump(dict(Y=ax.tolist(), o=o.tolist(), CA=CA.tolist()), open('wrist_axis.json','w'))
