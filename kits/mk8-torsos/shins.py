"""Old Style Space Knight bonus shin pads (Shin A/B/C): the right files, fitted by lining each up on the Mar Fil Assault
shin pad with the same shell (mk8_shins.py: 24 axis turns + ICP; A on pad 6 median 0.043, B on pad 3 0.134,
C on pad 1 0.000 - a plainer copy of it). fit = MarFil pad's Shin R fit @ registration.
The _L files are exact mirrors of _R (0.000 mm), so only R goes in: Knee Pads mirror for the left leg (mirrorLeft).
python shins.py SHIN_REG_JSON BONUS_DIR OUT"""
import json, os, shutil, sys
import numpy as np

REG, BON, OUT = sys.argv[1:4]
LIB = os.path.join(os.path.dirname(__file__), "..", "..", "library", "Mar Fil - Tacticus", "AssaultMarines-V2", "Knee Pads")
rows = json.load(open(os.path.join(OUT, "_rows.json"))) if os.path.exists(os.path.join(OUT, "_rows.json")) else []
for k, r in json.load(open(REG)).items():
    mf = json.load(open(os.path.join(LIB, f"MarFil Assault - Shin Pad {r['mf']}.sockets.json")))["fits"]["Shin R"]
    F = np.array(mf, float).reshape(4, 4) @ np.array(r["T"])
    part = f"OldStyle MK8 - Shin Pad {k}"; rel = os.path.join("Old Style Space Knight - Heresy", "MK8", "Knee Pads", part + ".stl")
    os.makedirs(os.path.dirname(os.path.join(OUT, rel)), exist_ok=True)
    shutil.copyfile(os.path.join(BON, f"Shin{k}_R.stl"), os.path.join(OUT, rel))
    src = f"new cults\\Old_style_space_knight_torso\\[BONUS]\\Shin{k}_R.stl"
    json.dump({"schemaVersion": 1, "part": f"Shin{k}_R", "category": "Knee Pads", "sockets": [],
               "fits": {"Shin R": [round(float(x), 6) for x in F.reshape(-1)]},
               "notes": {"Shin R": f"lined up on MarFil Assault - Shin Pad {r['mf']} (same shell, ICP median {r['median']:.3f} mm) and given its rig placement",
                         "left": f"Shin{k}_L is the exact mirror of this file: the left leg takes the mirror"},
               "original": {"name": f"Shin{k}_R", "folder": "[BONUS]", "path": src}},
              open(os.path.join(OUT, rel[:-4] + ".sockets.json"), "w"), indent=1)
    rows.append((rel.replace("/", "\\"), src, "Knee Pads", "Shin R"))
json.dump(rows, open(os.path.join(OUT, "_rows.json"), "w"), indent=0)
print(len(rows), "rows")
