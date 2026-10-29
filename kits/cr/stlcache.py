import sys, os, hashlib, numpy as np
sys.path.insert(0, "/home/claude/real")
import fitlib as F
C = "/home/claude/kits/cache/abs_"
def npz(path):
    key = hashlib.md5((path + str(os.path.getsize(path))).encode()).hexdigest()
    c = C + key + ".npz"
    if not os.path.exists(c):
        V, T = F.stl(path); np.savez(c, V=V.astype(np.float32), T=T.astype(np.int32))
    return c
def load(path):
    z = np.load(npz(path)); return z["V"].astype(float), z["T"]
