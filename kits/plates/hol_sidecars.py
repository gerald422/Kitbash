"""Merge the plate fits into the library holsters', pouches' and grenades' sidecars (Josh, Nov 3: plates only, grenades
too): category -> Plate Accessories; "Plate Hang L" fit from hol_fit.py; a right mirror variant like the AM-V2 sheaths
(align diag(-1,1,1), fit A·F·A). Mar Fil Outrider Holster 1 / 2 come as the maker's left and right files, exact mirrors
across file Y: the left file takes Plate Hang L, the right file Plate Hang R = A·F_left·M^-1 (M = diag(1,-1,1)), no
variants. The old belt fits go (Josh: plates only; with them the page reads the part as either side). Everything else in the sidecar is kept.
python hol_sidecars.py FITS_JSON OUT_DIR"""
import json, os, sys, numpy as np
FITS, OUT = sys.argv[1:3]
LIB = os.path.join(os.path.dirname(__file__), "..", "..", "library")
A = np.diag([-1.0, 1, 1, 1]); M = np.diag([1.0, -1, 1, 1])
fits = json.load(open(FITS)); byname = {k.split("\\")[-1][:-4]: (k, np.array(v["fit"]).reshape(4, 4)) for k, v in fits.items()}
flat = lambda m: [round(float(x), 6) for x in np.asarray(m).reshape(-1)]
RULE = ("hangs from the hip plate's Plate Hang like Josh's AM-V2 sheath: belt orientation (or from its shape), centred on "
        "the hang point, top 2.1 mm above it, deepest point 0.2 mm under the plate's outer face (Nov 3)")
PLATE = "Mar Fil - Tacticus\\AssaultMarines-V2\\Hip Plates\\MarFil Assault - Hip Plate L.stl"   # brought when the legs have no plate yet (like the sheaths)
OUTR = {"MarFil Outrider - Holster 1", "MarFil Outrider - Holster 2"}
rows = []
for nm, (rel, F) in byname.items():
    p = os.path.join(LIB, rel.replace("\\", "/")[:-4] + ".sockets.json")
    d = json.load(open(p, encoding="utf-8")); was = d.get("category")
    d["category"] = "Plate Accessories"; d.setdefault("fits", {}); d["adaptor"] = PLATE; notes = d.setdefault("notes", {})
    if not isinstance(notes, dict): notes = d["notes"] = {"old": notes}
    for k in ("Hip R", "Hip L", "Belt Front", "Belt Back"): d["fits"].pop(k, None)
    notes.pop("belt", None)
    notes["type"] = f"plate accessory (was {was}): hangs from the hip plate (Josh, Nov 3: plates only)"
    if nm in OUTR:
        FL = byname[nm + " L"][1]
        d["fits"]["Plate Hang R"] = flat(A @ FL @ np.linalg.inv(M))
        notes["Plate Hang R"] = "the maker's right file, the exact mirror (file Y) of the left one: mirror of its placement"
        d.pop("variants", None) if not d.get("variants") else None
    else:
        d["fits"]["Plate Hang L"] = flat(F); notes["Plate Hang L"] = RULE
        if not nm.startswith("MarFil Outrider - Holster"):
            base = nm[:-2] if nm.endswith(" L") else nm
            v = {"side": "R", "mirror": True, "align": flat(np.diag([-1.0, 1, 1, 1])), "name": base + " R", "title": base + " R",
                 "folder": rel.split("\\")[-2], "from": "mirror of the left placement (right hip plate)",
                 "sidecar": {"category": "Plate Accessories", "fits": {"Plate Hang R": flat(A @ F @ A)}, "sockets": []}}
            d["variants"] = [x for x in (d.get("variants") or []) if x.get("side") != "R"] + [v]
    q = os.path.join(OUT, rel.replace("\\", "/")[:-4] + ".sockets.json"); os.makedirs(os.path.dirname(q), exist_ok=True)
    json.dump(d, open(q, "w", encoding="utf-8"), indent=1)
    rows.append(rel)
json.dump(rows, open(os.path.join(OUT, "_changed.json"), "w"), indent=0)
print(len(rows), "sidecars")
