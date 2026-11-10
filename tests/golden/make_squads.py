#!/usr/bin/env python3
"""Pick the fixed test squads from the sidecars in library/ (seeded, so the list only changes when you re-run this).
One model per torso family, each wearing parts from other makers where the sockets allow: the cross-kit promise.
    python3 tests/golden/make_squads.py [N=14]   ->  tests/golden/squads.json
Re-running changes the squads, so record the golden again afterwards (Run checks.bat record)."""
import glob, json, os, random, sys
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 14
rng = random.Random(40000)
parts = {}
for f in sorted(glob.glob(os.path.join(R, "library", "**", "*.sockets.json"), recursive=True)):
    d = json.load(open(f, encoding="utf-8-sig"))
    rel = os.path.relpath(f, os.path.join(R, "library"))[:-len(".sockets.json")].replace(os.sep, "/")
    parts[rel] = dict(cat=d.get("category"), fits=set(d.get("fits") or {}),
                      socks={s.get("type") for s in d.get("sockets") or []}, maker=rel.split("/")[0].split(" - ")[0])
def pick(cat, fit, avoid=None, need=()):
    c = [p for p, e in parts.items() if e["cat"] in (cat if isinstance(cat, tuple) else (cat,)) and fit in e["fits"]
         and all(s in e["socks"] for s in need)]
    other = [p for p in c if parts[p]["maker"] != avoid]
    c = other if other and rng.random() < 0.6 else c
    return rng.choice(c) if c else None
torsos = [p for p, e in parts.items() if e["cat"] == "Chests" and {"Shoulder R", "Shoulder L", "Neck", "Back"} <= e["socks"]]
fam = {}
for t in torsos: fam.setdefault("/".join(t.split("/")[:2]), []).append(t)
keys = sorted(fam); rng.shuffle(keys)
squads = {}
for i, k in enumerate(keys[:N]):
    t = rng.choice(fam[k]); e = parts[t]; mk = e["maker"]; m = []
    add = lambda p, sock: p and m.append([p, parts[p]["cat"], sock])
    m.append([t, "Chests", None])
    waist = "Waist" if "Waist" in e["socks"] else "Flat Waist"
    legs = pick("Legs", waist, mk); add(legs, waist)
    for side in ("R", "L"):
        arm = pick("Arms", "Shoulder " + side, mk); add(arm, "Shoulder " + side)
        if arm and "Hand " + side in parts[arm]["socks"]: add(pick(("Melee", "Pistols"), "Hand " + side, mk), "Hand " + side)
        if arm and "Pad " + side in parts[arm]["socks"]: add(pick("Shoulder Pads", "Pad " + side, mk), "Pad " + side)
    add(pick("Heads", "Neck", mk), "Neck"); add(pick(("Backpacks", "Jump Packs"), "Back", mk), "Back")
    if legs and "Base" in parts[legs]["socks"]: add(pick("Bases", "Base"), "Base")
    squads["g%02d" % (i + 1)] = m
json.dump(squads, open(os.path.join(R, "tests", "golden", "squads.json"), "w", encoding="utf-8", newline="\n"), indent=1)
print(len(squads), "models,", sum(len(v) for v in squads.values()), "parts; makers:",
      sorted({parts[p]["maker"] for v in squads.values() for p, _, _ in v}))
