import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn')
import numpy as np, json, stlcache
import conv
from render_cross import C_T, C_TN
from tn_sockets import sockets_for
U = "/mnt/user-data/uploads/new cults/"
fits = json.load(open('/home/claude/kits/tn/legs/sample_fits.json'))
tor = "TurtleNinja's Mk6 Assault Addon 1/Torsos/Mk6_Assault_Torso_A_2.stl"
S, f = sockets_for(tor); W = conv.KB @ np.linalg.inv(S['Flat Waist'])
models = []
for i, (rel, F) in enumerate(fits.items()):
    if not __import__('os').path.exists(U + rel): continue
    F = np.array(F).reshape(4, 4)
    models.append(dict(name=f'S{i:02d}', items=[[stlcache.npz(U + "Turtle Ninja/" + tor), W.ravel().tolist(), C_T], [stlcache.npz(U + rel), (W @ S['Flat Waist'] @ F).ravel().tolist(), C_TN]]))
json.dump({"out": "/home/claude/kits/tn/rls", "res": 300, "pad": 1.05, "models": models, "views": {"front": [0, 1, 0], "side": [1, 0, 0]}}, open('j_ls.json', 'w'))
json.dump([m['name'] for m in models], open('/home/claude/kits/tn/rls_names.json', 'w')); json.dump(list(fits), open('/home/claude/kits/tn/rls_rels.json', 'w'))
