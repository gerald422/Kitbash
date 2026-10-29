import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr')
import geo, numpy as np, json
LJ = json.load(open('/home/claude/kits/legs_josh.json'))['legs']
def belt_top(rel, M, cy=0.571):
    V,T = geo.load(rel); S = geo.surf(np.asarray(V,float),T,400000)
    W = S @ M[:3,:3].T + M[:3,3]
    ang = np.degrees(np.arctan2(W[:,0], W[:,1]-cy)); r = np.hypot(W[:,0], W[:,1]-cy)
    out = {}
    for name, sec in (('front', np.abs(ang) < 35), ('side', (np.abs(np.abs(ang)-90) < 30)), ('back', np.abs(ang) > 145)):
        zs = np.arange(22.0, 28.0, 0.1); last = None
        for z in zs:
            k = sec & (np.abs(W[:,2]-z) < 0.06)
            if k.sum() < 5: continue
            if np.percentile(r[k], 95) > 4.85: last = z
        out[name] = last
    return out
if __name__ == '__main__':
    for rel in LJ:
        if 'Mirrored' in rel: continue
        print(rel.split('/')[-1][:16], belt_top(rel, np.array(LJ[rel]['M'])))
