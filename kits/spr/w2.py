import sys, json, numpy as np
sys.argv = ["x"]
import hands as H
sel = json.load(open("w/sel_raw.json")); todo = json.load(open("w/worker2.json"))
out = {}
for rel in todo:
    info, ds = H.find(rel, sel[rel])
    out[rel] = dict(info, domes=[{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in d.items()} for d in ds])
    print(rel, len(ds), flush=True)
    json.dump(out, open("w/hands_w2.json", "w"), indent=0)
print("W2DONE")
