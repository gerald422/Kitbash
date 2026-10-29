import json, os, numpy as np
OUT = "/home/claude/kits/out113/stage_spr/Springles/"
P = json.load(open("w/packs.json"))
for rel, p in P.items():
    d = {"schemaVersion": 1, "part": os.path.basename(rel)[:-4], "category": "Backpacks", "scale": 1.1, "sockets": [],
         "fits": {"Back": [round(float(x), 6) for x in np.array(p["fit"]).ravel()]},
         "notes": {"Back": "mount plate (%.0f mm2) flat on the back, plate centres together (as Turtle Ninja packs)" % p["plate"]}}
    f = OUT + rel[:-4] + ".sockets.json"; os.makedirs(os.path.dirname(f), exist_ok=True); json.dump(d, open(f, "w"))
print(len(P), "pack sidecars")
