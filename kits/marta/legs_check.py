import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn'); sys.path.insert(0,'/home/claude/kits/cr/dev')
import numpy as np, json, os, stlcache as sc, flats, conv
from topface import top_face
from flatface import frame
from tn_sockets import sockets_for
from render_cross import C_T, C_MF
U="/mnt/user-data/uploads/new cults/Marta/"
L=json.load(open('ln_paths.json'))
tor="TurtleNinja's Mk2-6 Builder/Mk6/Torsos/Upper A 9.stl"; S,f=sockets_for(tor); W=conv.KB@np.linalg.inv(S['Flat Waist'])
TN="/mnt/user-data/uploads/new cults/Turtle Ninja/"
models=[]; Lm=lambda x: x.ravel().tolist()
for i,p in enumerate(L):
    V,T=sc.load(U+p); FL=[(a,n,c) for a,n,c,o,s in flats.flats(V,T,min_area=1.0)]
    A,n,c=top_face(FL, ytop=float(V[:,1].max()))
    fit=np.linalg.inv(frame(c,n,[0,0,1]))
    models.append(dict(name='M%d'%i, items=[[sc.npz(TN+tor),Lm(W),C_T],[sc.npz(U+p),Lm(W@S['Flat Waist']@fit),C_MF]]))
json.dump({"out":"/home/claude/kits/marta/rc","res":200,"pad":1.05,"models":models,"views":{"front":[0,1,0.1],"side":[1,0,0.1]}},open('jc.json','w'))
