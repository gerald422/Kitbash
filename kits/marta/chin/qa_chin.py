import sys; sys.path.insert(0,'/home/claude/real'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits')
import fitlib as F, numpy as np, json, stlcache as sc
U="/mnt/user-data/uploads/new cults/"
LEGS=U+"All Mar All the time/AssaultMarines-V2/AssaultMarines-V2/RawSTL/Legs/29-Legs-2.stl"
V,T=F.stl(LEGS); f=F.find_shin_points(V,T); fr={}
for ea,eb,top,op in f:
    fr['R' if top[0]>0 else 'L']=F.shin_frame(ea,eb,top,op)
print(list(fr))
R=json.load(open('chin_fits.json')); items=list(R.items())
Ls=[(k,v) for k,v in items if v['side']=='L']; Rs=[(k,v) for k,v in items if v['side']=='R']
models=[]
for i in range(max(len(Ls),len(Rs))):
    it=[[sc.npz(LEGS),np.eye(4).ravel().tolist(),[0.6,0.68,0.85,1]]]; name=[]
    for lst in (Ls,Rs):
        if i<len(lst):
            k,v=lst[i]; it.append([sc.npz(U+'Marta/'+k),(fr[v['side']]@np.array(v['fit'])).ravel().tolist(),[0.95,0.5,0.15,1]]); name.append(k.split('/')[-1][:-4])
    models.append(dict(name='c%d'%i,items=it)); 
json.dump([m['name'] for m in models],open('cn.json','w'))
json.dump({"out":"/home/claude/kits/marta/chin/r","res":220,"pad":1.05,"models":models,"views":{"front":[0,1,0.15],"side":[1,0.3,0.1],"sideL":[-1,0.3,0.1]}},open('jc.json','w'))
lab=[]
for i in range(len(models)):
    a=Ls[i][0].split('/')[-1][:-4] if i<len(Ls) else ''; b=Rs[i][0].split('/')[-1][:-4] if i<len(Rs) else ''; lab.append(a+' | '+b)
json.dump(lab,open('cl.json','w'))
