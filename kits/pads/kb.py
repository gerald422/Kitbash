"""Index + preview helpers for the pad audit (numpy only)."""
import json, struct, numpy as np, os
LIB = "/home/claude/work/pads/lib/_builder"
IDX = json.load(open("/mnt/user-data/uploads/d/Kitbash Library/_builder/index.json"))
P = IDX["parts"]; BY = {e["name"]: e for e in P}; BYID = {e["id"]: e for e in P}
MX = np.diag([-1.0, 1, 1, 1])
def M(v): return np.array(v, float).reshape(4, 4)
def conj(m): return MX @ m @ MX
def prev(e):
    b = open(os.path.join(LIB, e["prev"]), "rb").read()
    assert b[:4] == b"KBP1"; nv, nt = struct.unpack("<II", b[4:12])
    V = np.frombuffer(b, np.float32, nv * 3, 12).reshape(-1, 3).astype(float)
    T = np.frombuffer(b, np.uint32, nt * 3, 12 + nv * 12).reshape(-1, 3)
    return V, T
def xf(A, V): return V @ A[:3, :3].T + A[:3, 3]
def sock(e, t):
    for s in e.get("sockets", []):
        if s["t"] == t: return M(s["m"])
    return None
def fit(e, t):
    f = e.get("fits", {}).get(t); return None if f is None else M(f)
def rot(A): u, s, vt = np.linalg.svd(A[:3, :3]); return u @ vt
def ang(R): return float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))))
