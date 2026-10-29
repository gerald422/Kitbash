import sys, numpy as np, json
sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/real')
import stlcache, fitlib as F
from scipy.spatial import cKDTree
np.set_printoptions(precision=3, suppress=True)
U="/mnt/user-data/uploads/new cults/Turtle Ninja/"; P6=U+"TurtleNinja's Mk2-6 Builder/Mk6/Powerpacks/"
def umeyama(P,Q):
    cp,cq=P.mean(0),Q.mean(0); X=P-cp; Y=Q-cq; Uu,S,Vt=np.linalg.svd(X.T@Y)
    D=np.diag([1,1,np.sign(np.linalg.det(Vt.T@Uu.T))]); R=Vt.T@D@Uu.T; s=(S*np.diag(D)).sum()/(X**2).sum(); return s,R,cq-s*R@cp
def sicp(src,tree,s,R,t,iters=60,keep=0.8):
    for _ in range(iters):
        P=s*src@R.T+t; d,i=tree.query(P); m=d<=np.quantile(d,keep); s,R,t=umeyama(src[m],tree.data[i[m]])
    d,_=tree.query(s*src@R.T+t); return s,R,t,d
Vm,Tm=stlcache.load(P6+"Powerpack 1.stl"); Sm=F.surf(Vm,Tm,40000); tree=cKDTree(Sm)
R0=np.array(json.load(open('decomp.json'))["Mk6 Powerpack 1.stl"])
V,T=stlcache.load(P6+"Mk6 Powerpack 1.stl"); S=F.surf(V,T,8000)
s,R,t,d=sicp(S,tree,1.0,R0[:3,:3],R0[:3,3])
print('pack scale %.4f median %.3f p80 %.3f'%(s,np.median(d),np.quantile(d,0.8)))
Vv,Tv=stlcache.load(P6+"Powerpack Vox Caster 1.stl"); Sv=F.surf(Vv,Tv,8000)
Rv=np.array(json.load(open('decomp.json'))['vox'])
s2,R2,t2,d2=sicp(Sv,tree,1.0,Rv[:3,:3],Rv[:3,3])
print('vox scale %.4f median %.3f p80 %.3f'%(s2,np.median(d2),np.quantile(d2,0.8)))
