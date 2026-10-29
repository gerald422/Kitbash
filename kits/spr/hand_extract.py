import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits/cr'); sys.path.insert(0, '/home/claude/real')
import stlcache, fitlib as F
from scipy.spatial import cKDTree
U = "/mnt/user-data/uploads/new cults/Springles/"
SCR = "/tmp/claude-0/-home-claude/3c0770af-36e9-58fc-b7f7-70184e2b5d36/scratchpad/"
def hand_part(withh, noh, out):
    V1, T1 = stlcache.load(U + withh); V0, T0 = stlcache.load(U + noh)
    S0 = F.surf(V0, T0, 80000, 1); S1 = F.surf(V1, T1, 8000, 2)
    t0 = S0.mean(0) - S1.mean(0)
    # same orientation (both lying on the bed): translation init, then ICP with trimming (hands are extra)
    R, t, d = F.icp(S1, cKDTree(S0), np.eye(3), t0, 40, 0.6)
    print(withh, "align median %.3f" % np.median(np.sort(d)[:len(d) // 2]))
    tree = cKDTree(S0); c = V1[T1].mean(1) @ R.T + t
    dd, _ = tree.query(c); k = dd > 0.25
    T2 = T1[k]; u, inv = np.unique(T2, return_inverse=True)
    np.savez(SCR + out, V=(V1[u] @ R.T + t).astype(np.float32), T=inv.reshape(-1, 3).astype(np.int32))
    np.savez(SCR + out.replace(".npz", "_gun.npz"), V=V0.astype(np.float32), T=T0.astype(np.int32))
    return R, t
R, t = hand_part("umbra bolters/bolter/umbra bolter 1 hand grip.stl", "umbra bolters/bolter/umbra bolter no hands.stl", "hand_grip.npz")
R, t = hand_part("umbra bolters/bolter/umbra bolter 1 hand foregrip.stl", "umbra bolters/bolter/umbra bolter no hands.stl", "hand_fore.npz")
R, t = hand_part("special weapons/plasma pistol/plasma pistol.stl", "special weapons/plasma pistol/plasma pistol no hands.stl", "hand_pp.npz")
models = [dict(name=n, items=[[SCR + n + ".npz", np.eye(4).ravel().tolist(), [0.9, 0.6, 0.3, 1]], [SCR + n + "_gun.npz", np.eye(4).ravel().tolist(), [0.6, 0.6, 0.7, 1]]]) for n in ("hand_grip", "hand_fore", "hand_pp")]
models += [dict(name=n + "_only", items=[[SCR + n + ".npz", np.eye(4).ravel().tolist(), [0.9, 0.6, 0.3, 1]]]) for n in ("hand_grip", "hand_fore", "hand_pp")]
json.dump({"out": "/home/claude/kits/spr/rh", "res": 300, "pad": 1.1, "models": models,
           "views": {"py": [0, 1, 0.2], "my": [0, -1, 0.2], "px": [1, 0.2, 0.3], "mx": [-1, 0.2, 0.3]}}, open("j_hand.json", "w"))
