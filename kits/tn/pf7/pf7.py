import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/cr/dev'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, stlcache, flats
from topface import merge_flats
from flatface import frame
import conv
np.set_printoptions(precision=3, suppress=True)
A="/mnt/user-data/uploads/new cults/Turtle Ninja/TurtleNinja's Mk7-8 Assault Intercessors Addon 1/Arms/"
QI={s: np.linalg.inv(conv.Q['Shoulder '+s]) for s in 'RL'}
MX=np.diag([-1.,1,1])
def tf(M,P): return P@M[:3,:3].T+M[:3,3]
def flats_of(V,T): return merge_flats([(a,nn,c) for a,nn,c,o,s in flats.flats(V,T,min_area=1.0)])
def dirs(P, ax):
    """upper-arm direction (points 4-8 mm from the joint, across the disc axis) and the far end (fist), in socket coordinates"""
    d=np.linalg.norm(P,axis=1); q=P[(d>4)&(d<8)].mean(0); q-=(q@ax)*ax; q/=np.linalg.norm(q)
    far=P[d>np.quantile(d,0.97)].mean(0); return q, far
# reference arm: Arm Single A_1 by the arm rule
Vr,Tr=stlcache.load(A+"Mk7_Arm_Single_A_1.stl")
a,n,c=max([m for m in flats_of(Vr,Tr) if abs(m[1][0])>0.98 and m[0]>6], key=lambda m:m[0])
Fr=QI['R']@np.linalg.inv(frame(c,-n,[0,1,0]))
ax=QI['R'][:3,:3]@np.array([0,0,1.])
uref,_=dirs(tf(Fr,Vr),ax); print('ref upper dir (socket R)', uref, 'axis', ax)
SW=conv.S_AM
out={}
for name in ["Mk7_Powerfist_A_1","Mk7_Powerfist_A_2","Mk7_Powerfist_B_1","Mk7_Powerfist_B_2","Mk7_Powerfist_B_11","Mk7_Powerfist_B_21"]:
    V,T=stlcache.load(A+name+'.stl')
    a,n,c=max([m for m in flats_of(V,T) if 10<m[0]<18 and m[2][0]>14], key=lambda m:m[0])
    best={}
    for s in 'RL':
        axs=QI[s][:3,:3]@np.array([0,0,1.]); ur=uref if s=='R' else MX@uref
        res=[]
        for th in range(0,360,1):
            h=np.array([np.cos(np.radians(th)),np.sin(np.radians(th)),0.3])
            if abs(h@(-n))>0.95*np.linalg.norm(h): continue
            Fi=QI[s]@np.linalg.inv(frame(c,-n,h)); u,far=dirs(tf(Fi,V),axs)
            res.append((np.degrees(np.arccos(np.clip(u@ur,-1,1))),th,Fi,far))
        e,th,Fi,far=min(res,key=lambda r:r[0])
        fw=(SW['Shoulder '+s]@np.append(far,1))[:3]
        best[s]=(e,Fi,fw)
        print(name,s,'disc A %.1f'%a,'swing err %.2f'%e,'fist at (world)',fw.round(1))
    out[name]={s:dict(err=best[s][0],fit=best[s][1].tolist(),fist=best[s][2].tolist()) for s in 'RL'}
json.dump(out,open('pf7.json','w'))
