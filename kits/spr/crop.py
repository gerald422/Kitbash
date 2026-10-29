import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); import stlcache
U = "/mnt/user-data/uploads/new cults/Springles/"
AF = json.load(open("arm_fits.json"))
def crop_npz(path, centre, rad, out):
    V, T = stlcache.load(path); c = V[T].mean(1); k = np.linalg.norm(c - centre, axis=1) < rad
    T2 = T[k]; u, inv = np.unique(T2, return_inverse=True)
    np.savez(out, V=V[u].astype(np.float32), T=inv.reshape(-1, 3).astype(np.int32)); return out
models = []
for i, rel in enumerate(["patternC arms/tactical arms/patternC ranged Rarm 1.stl", "patternC arms/melee arms/patternC melee Rarm 3.stl", "patternS arms/heavy weapons/patternS heavy Rarm 2.stl"]):
    V, T = stlcache.load(U + rel); a = AF[rel]; F = np.array(a["fit"]); j = np.linalg.inv(F)[:3, 3] / a["scale"]
    far = V[np.argmax(np.linalg.norm(V - j, axis=1))]
    # wrist end centre: mean of points within 3mm of the farthest point
    p = crop_npz(U + rel, far, 6, "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/arm%d.npz" % i)
    models.append(dict(name="a%d" % i, items=[[p, np.eye(4).ravel().tolist(), [0.9, 0.6, 0.3, 1]]]))
for i, rel in enumerate(["umbra bolters/bolter/umbra bolter 1 hand grip.stl"]):
    V, T = stlcache.load(U + rel)
    far = V[np.argmax(V[:, 0])]   # grip hand at the +x end (py view right side)
    p = crop_npz(U + rel, far, 7, "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/hand%d.npz" % i)
    models.append(dict(name="h%d" % i, items=[[p, np.eye(4).ravel().tolist(), [0.9, 0.8, 0.5, 1]]]))
json.dump({"out": "/home/claude/kits/spr/rc", "res": 300, "pad": 1.1, "models": models,
           "views": {"a": [1, 0.3, 0.4], "b": [-1, -0.3, 0.4], "c": [0.2, -1, 0.3], "d": [0.3, 1, -0.4]}}, open("j_crop.json", "w"))
