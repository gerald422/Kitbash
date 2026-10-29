exec(open('pf7.py').read().split("SW=conv.S_AM")[0])
from render_cross import C_T, C_TN, C_MF
from tn_sockets import sockets_for
TN="/mnt/user-data/uploads/new cults/Turtle Ninja/"
tor="TurtleNinja's Mk7-8 Assault Intercessors Addon 1/Torsos/Mk7_Torso_Jumppack_A_9.stl"; S,f=sockets_for(tor); W=conv.KB@np.linalg.inv(S['Flat Waist'])
out=json.load(open('pf7.json')); O=[0.95,0.5,0.15,1]
L=lambda x: np.asarray(x).ravel().tolist()
models=[]
for name in ["Mk7_Powerfist_A_1","Mk7_Powerfist_B_1","Mk7_Powerfist_B_11"]:
    for s in 'RL':
        o='L' if s=='R' else 'R'
        Fa=Fr if o=='R' else None
        items=[[stlcache.npz(TN+tor),L(W),C_T],[stlcache.npz(A+name+'.stl'),L(W@S['Shoulder '+s]@np.array(out[name][s]['fit'])),O]]
        if o=='R': items.append([stlcache.npz(A+"Mk7_Arm_Single_A_1.stl"),L(W@S['Shoulder R']@Fr),C_TN])
        models.append(dict(name=f"{name[12:]}_{s}",items=items))
json.dump({"out":"/home/claude/kits/tn/pf7/r","res":260,"pad":1.05,"models":models,"views":{"front":[0,1,0.1],"top":[0,0.3,1],"out":[1 ,0.3,0.1],"outl":[-1,0.3,0.1]}},open('j.json','w'))
