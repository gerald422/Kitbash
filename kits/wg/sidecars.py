"""WarGame Exclusive (WargamesPrint 'BL' sets, Nov 9): source sidecars beside the files in D:\\new cults.
Files stand Z up, front -Y, at Mar Fil scale. Heads and helmets get the Neck fit from Josh's AM helmet seat
(kits/rw_spr/heads.py), pauldrons the Pad R fit from his pad 62 (kits/rw_spr/pads.py, left = mirror).
Shoulder shields, necklaces and arm/knee/leg plates are filed without a fit (Josh: no spots for them yet).
Skipped: Pres (supported) copies, the duplicate 'BL-PAULDRONS-4 (1)', CONNECTORS_* (plate pegs).
python sidecars.py HEADS.json PADS.json OUTDIR"""
import json, os, sys, glob
H, P, OUT = sys.argv[1:4]
U = "/mnt/user-data/uploads/d/new cults/"
heads, pads = json.load(open(H)), json.load(open(P))
NOFIT = {"SHOULDER_SHIELDS": ("Unsorted", "shoulder shield (a pad ornament): no spot for it yet"),
         "NECKLACE": ("Unsorted", "necklace: no spot for it yet"),
         "ARM_PROTECTION": ("Forearm Armour", "forearm plate: no spot for it yet"),
         "KNEE_PROTECTION": ("Knee Pads", "knee plate: no fit yet"),
         "LEG_PROTECTION": ("Unsorted", "thigh plate: no spot for it yet")}
made = []
for p in sorted(glob.glob(U + "WarGame Exclusive/BL-*/*.stl")):
    rel = os.path.relpath(p, U)
    if "(1)" in rel or os.path.basename(p).startswith("CONNECTORS"): continue
    stem = os.path.basename(p)[:-4]; folder = os.path.basename(os.path.dirname(p))
    d = {"schemaVersion": 1, "part": stem, "sockets": [], "fits": {}, "notes": {},
         "original": {"name": stem, "folder": folder, "path": rel.replace("/", "\\")}}
    if rel in heads:
        r = heads[rel]; d["category"] = "Heads"; d["fits"]["Neck"] = r["fit"]
        d["notes"]["Neck"] = "Josh's Assault helmet 1 neck seat matched onto it (match %.3f mm)" % r["med"]
    elif rel in pads and rel.endswith("/PAD_7.stl"):
        # the skull-on-a-pole pad: 62's shell only matches it at the 0.85 scale floor and it lands turned, cutting 1.6 mm
        d["category"] = "Shoulder Pads"; d["notes"]["category"] = "filed without a fit (Nov 9): the pad-62 match doesn't hold for it; place it by eye"
    elif rel in pads:
        r = pads[rel]; d["category"] = "Shoulder Pads"; d["fits"]["Pad R"] = r["fit"]
        d["notes"]["Pad"] = "Josh's pad 62 matched onto it (x%.2f, match %.3f mm), his Pad R fit carried across about 62's shell centre" % (r["scale_vs_62"], r["med"])
        if r.get("lift"): d["notes"]["Pad"] += "; pushed out %.2f mm off the shoulder (thicker inside than 62; padlift.py: %.2f mm into Arm 1A R after)" % (r["lift"], r["cut_after"])
    else:
        k = next(k for k in NOFIT if stem.startswith(k)); d["category"], why = NOFIT[k]
        d["notes"]["category"] = "filed without a fit (Nov 9): " + why
    o = os.path.join(OUT, rel[:-4] + ".sockets.json"); os.makedirs(os.path.dirname(o), exist_ok=True)
    json.dump(d, open(o, "w"), indent=1); made.append([rel, d["category"], bool(d["fits"])])
# library names: WargamesPrint - Tacticus\\BL\\<type>\\WargamesPrint BL - <Name N>
NICE = {"HELMET": "Helmet", "HEAD": "Head", "PAD": "Pad", "SHOULDER_SHIELDS": "Shoulder Shield", "NECKLACE": "Necklace",
        "ARM_PROTECTION": "Arm Plate", "KNEE_PROTECTION": "Knee Plate", "LEG_PROTECTION": "Leg Plate"}
for m in made:
    stem = os.path.basename(m[0])[:-4]; k, n = stem.rsplit("_", 1)
    m.append("WargamesPrint - Tacticus\\BL\\%s\\WargamesPrint BL - %s %s.stl" % (m[1], NICE[k], n))
json.dump(made, open(os.path.join(OUT, "list.json"), "w"), indent=0)
import collections; print(len(made), collections.Counter((m[1], m[2]) for m in made))
