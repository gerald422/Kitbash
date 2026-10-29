"""Compare two replay logs: every send lands on the same socket in the same place."""
import json, sys, math
import numpy as np
a, b = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
bad = 0
for x, y in zip(a, b):
    why = []
    if x.get("sock") != y.get("sock"): why.append(f"socket {x.get('sock')} vs {y.get('sock')}")
    if x.get("orig") != y.get("orig"): why.append(f"name {x.get('orig')} vs {y.get('orig')}")
    if "M" in x and "M" in y:
        A, B = np.array(x["M"]), np.array(y["M"])
        d = np.linalg.norm(A[:3, 3] - B[:3, 3]); R = A[:3, :3] @ B[:3, :3].T
        # (the angle from the Frobenius norm: acos of the trace is too coarse near 0 for 5-decimal logs)
        ang = math.degrees(2 * math.asin(min(1.0, np.linalg.norm(R - np.eye(3)) / (2 * math.sqrt(2)))))
        if d > 0.01 or ang > 0.05: why.append(f"moved {d:.3f} mm {ang:.3f} deg")
    elif ("M" in x) != ("M" in y): why.append("one has no pose")
    if why:
        bad += 1; print(f"  DIFF #{x['i']} {x['rel'].split('/')[-1]}: " + "; ".join(why))
print(f"{len(a)} vs {len(b)} sends, {bad} different" + ("" if len(a) == len(b) else "  (COUNTS DIFFER)"))
