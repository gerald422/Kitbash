import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr')
import json, numpy as np, stlcache
U = "/mnt/user-data/uploads/new cults/Turtle Ninja/"
P6 = "TurtleNinja's Mk2-6 Builder/Mk6/Powerpacks/"; P4 = "TurtleNinja's Mk4 Tactical Squad/Powerpacks/"
I = np.eye(4).ravel().tolist(); G=[0.8,0.8,0.8,1]; O=[0.95,0.5,0.15,1]
models = [
 dict(name='mk6pack1', items=[[stlcache.npz(U+P6+"Mk6 Powerpack 1.stl"), I, G]]),
 dict(name='powerpack1', items=[[stlcache.npz(U+P6+"Powerpack 1.stl"), I, G]]),
 dict(name='banner1', items=[[stlcache.npz(U+P6+"Powerpack Banner 1.stl"), I, O]]),
 dict(name='vox1', items=[[stlcache.npz(U+P6+"Powerpack Vox Caster 1.stl"), I, O]]),
 dict(name='mk4pack_vox', items=[[stlcache.npz(U+P4+"Mk4_Powerpack_1.stl"), I, G], [stlcache.npz(U+P4+"Mk4_Powerpack_Voxcaster.stl"), I, O]]),
 dict(name='mk4banner', items=[[stlcache.npz(U+P4+"Mk4_Powerpack_Banner.stl"), I, O]]),
]
json.dump({"out": "/home/claude/kits/tn/rtop", "res": 300, "pad": 1.1, "models": models,
           "views": {"pz": [0, 0, 1], "nz": [0, 0, -1], "px": [1, 0, 0.001], "py": [0.001, 1, 0.3]}}, open('j_top.json', 'w'))
