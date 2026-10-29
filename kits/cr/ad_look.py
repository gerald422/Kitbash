import sys, numpy as np
sys.path.insert(0, "/home/claude/real"); sys.path.insert(0, "/home/claude/kits")
import fitlib as F, disc
D = "/mnt/user-data/uploads/new cults/body adaptor/"
for i in range(1, 7):
    V, T = F.stl(D + f"lower_body_(torso)_{i}.stl")
    cen, n, a = disc.tri_info(V, T)
    lo, hi = V.min(0), V.max(0)
    # big flat faces by normal direction
    out = []
    for name, d in [("+Z", [0,0,1]), ("-Z", [0,0,-1]), ("+Y", [0,1,0]), ("-Y", [0,-1,0])]:
        k = (n @ np.array(d, float)) > 0.995
        if k.any():
            z = cen[k] @ np.array(d, float)
            # area at the extreme plane
            zz = np.round(z, 1); vals, inv = np.unique(zz, return_inverse=True)
            A = np.bincount(inv, a[k]); j = A.argmax()
            out.append(f"{name}: plane {vals[j]:.2f} area {A[j]:.1f}")
    print(i, len(T), "lo", lo.round(2), "hi", hi.round(2), "size", (hi-lo).round(2)); print("   ", "; ".join(out))
