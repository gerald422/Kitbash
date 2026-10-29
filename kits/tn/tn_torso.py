"""Turtle Ninja flat torsos: joint faces -> sockets that match Mar Fil's conventions."""
import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr')
import numpy as np, json, os, stlcache, flats, geo
from flatface import frame
from tn_faces import faces
TN = "/mnt/user-data/uploads/new cults/Turtle Ninja/"
def torso_faces(V, T):
    bot, up, sh, axis, side, tops = faces(V, T)
    back = max([f for f in side if f[0] > 8], key=lambda f: f[0], default=None)
    b0 = bot[2]
    def rdist(c): d = c - b0; return float(np.linalg.norm(d - (d @ up) * up))
    necks = [f for f in tops if rdist(f[2]) < 3.0 and f[0] > 4]
    neck = max(necks, key=lambda f: f[0], default=None)
    front = -back[1] if back is not None else None
    # right shoulder: marine faces `front`, up `up` -> right = front x up
    right = np.cross(front, up)
    shR, shL = (sh[0], sh[1]) if sh[0][1] @ right > 0 else (sh[1], sh[0])
    return dict(bottom=bot, up=up, front=front, right=right, shR=shR, shL=shL, back=back, neck=neck)
if __name__ == '__main__':
    out = {}
    for p in json.load(open('flat_torsos.json')):
        V, T = stlcache.load(TN + p); f = torso_faces(V, T)
        ok = 15 < f['shR'][0] < 20 and f['back'] is not None and f['neck'] is not None
        out[p] = {k: ([float(v[0]), v[1].tolist(), v[2].tolist()] if isinstance(v, tuple) else (v.tolist() if v is not None else None)) for k, v in f.items()}
        print('%-40s %s shR %.1f %s back %.1f neck %s front %s' % (p.split('/')[-1][:40], 'ok ' if ok else 'BAD', f['shR'][0], f['shR'][1].round(2), f['back'][0] if f['back'] else -1, ('%.1f h%.2f' % (f['neck'][0], (f['neck'][2] - f['bottom'][2]) @ f['up'])) if f['neck'] else None, f['front'].round(2) if f['front'] is not None else None))
    json.dump(out, open('torso_faces.json', 'w'), indent=0)
