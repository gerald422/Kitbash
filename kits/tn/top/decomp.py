import sys, numpy as np, json
sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/real')
import stlcache, fitlib as F
from scipy.spatial import cKDTree
np.set_printoptions(precision=3, suppress=True)
U="/mnt/user-data/uploads/new cults/Turtle Ninja/"; P6=U+"TurtleNinja's Mk2-6 Builder/Mk6/Powerpacks/"
Vm,Tm=stlcache.load(P6+"Powerpack 1.stl"); Sm=F.surf(Vm,Tm,40000)
res={}
for n in ["Mk6 Powerpack 1.stl","Mk6 Powerpack 2.stl","Mk6 Hellblaster Pack 1.stl"]:
    try: V,T=stlcache.load(P6+n)
    except Exception as e: print(n, e); continue
    S=F.surf(V,T,6000)
    R,t,d=F.best_fit(S,Sm)
    print(n,'median %.3f p90 %.3f'%(np.median(d),np.quantile(d,0.9)))
    res[n]=F.pose(R,t).tolist()
best=min(res, key=lambda k: 0)
# remove pack-explained points
R=np.array(res["Mk6 Powerpack 1.stl"]) 
V,T=stlcache.load(P6+"Mk6 Powerpack 1.stl"); Sp=F.surf(V,T,60000)@R[:3,:3].T+R[:3,3]
d,_=cKDTree(Sp).query(Sm); rest=Sm[d>0.3]; print('rest', len(rest), rest.min(0), rest.max(0))
Vv,Tv=stlcache.load(P6+"Powerpack Vox Caster 1.stl"); Sv=F.surf(Vv,Tv,6000)
tree=cKDTree(rest); best=None
for R0 in F.rots24():
    t0=rest.mean(0)-R0@Sv.mean(0)
    Rr,tt,dd=F.icp(Sv,tree,R0,t0,40)
    if best is None or np.median(dd)<best[0]: best=(np.median(dd),Rr,tt)
Rr,tt,dd=F.icp(Sv,tree,best[1],best[2],80)
print('vox median %.3f p90 %.3f'%(np.median(dd),np.quantile(dd,0.9)))
res['vox']=F.pose(Rr,tt).tolist()
json.dump(res,open('decomp.json','w'))
