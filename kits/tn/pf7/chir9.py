exec(open('pf7.py').read().split("SW=conv.S_AM")[0])
from scipy.spatial import cKDTree
sys.path.insert(0,'/home/claude/real'); import fitlib as FL
out=json.load(open('pf7.json'))
Pr=tf(Fr, FL.surf(Vr,Tr,30000)); Rr=Pr[np.linalg.norm(Pr,axis=1)<9]; tree=cKDTree(Rr)
for name,v in out.items():
    V,T=stlcache.load(A+name+'.stl'); S=FL.surf(V,T,30000)
    for s in 'RL':
        P=tf(np.array(v[s]['fit']),S)
        if s=='L': P=P@MX.T
        Q=P[np.linalg.norm(P,axis=1)<8]
        d,_=tree.query(Q); R,t,d2=FL.icp(Q,tree,np.eye(3),np.zeros(3),30)
        print(name,s,'direct median %.3f'%np.median(d),'after icp %.3f rot %.1f'%(np.median(d2),FL.ang(R)))
