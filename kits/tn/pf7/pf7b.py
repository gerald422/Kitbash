exec(open('pf7.py').read().split("# reference arm")[0])
SW=conv.S_AM
tgt={'R': np.array([0.2,0.15,-0.97]), 'L': np.array([-0.2,0.15,-0.97])}
for s in 'RL': tgt[s]/=np.linalg.norm(tgt[s])
out={}
for name in ["Mk7_Powerfist_A_1","Mk7_Powerfist_A_2","Mk7_Powerfist_B_1","Mk7_Powerfist_B_2","Mk7_Powerfist_B_11","Mk7_Powerfist_B_21"]:
    V,T=stlcache.load(A+name+'.stl')
    a,n,c=max([m for m in flats_of(V,T) if 10<m[0]<18 and m[2][0]>14], key=lambda m:m[0])
    out[name]={}
    for s in 'RL':
        Sr=SW['Shoulder '+s]; axs=QI[s][:3,:3]@np.array([0,0,1.])
        res=[]
        for th in range(0,360,1):
            h=np.array([np.cos(np.radians(th)),np.sin(np.radians(th)),0.3])
            Fi=QI[s]@np.linalg.inv(frame(c,-n,h)); P=tf(Sr@Fi,V); j=Sr[:3,3]
            d=np.linalg.norm(P-j,axis=1); u=P[(d>4)&(d<8)].mean(0)-j; u/=np.linalg.norm(u)
            res.append((np.degrees(np.arccos(np.clip(u@tgt[s],-1,1))),th,Fi,P[d>np.quantile(d,0.97)].mean(0)))
        e,th,Fi,far=min(res,key=lambda r:r[0])
        out[name][s]=dict(err=e,fit=Fi.tolist(),fist=far.tolist())
        print(name,s,'upper err %.1f'%e,'fist',far.round(1))
json.dump(out,open('pf7b.json','w'))
