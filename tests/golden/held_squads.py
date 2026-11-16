#!/usr/bin/env python3
"""Squads for a before / after check of Move origins (notes 105, 107, 108): the parts an origins config would move,
each built on a torso (packs on its Back, weapons in the hands of one arm put on both shoulders). No Blender.

    python tests/golden/held_squads.py ORIGINS_CONFIG --torso REL --arm REL [--lib LIB] [--most 60] [--out FILE]

  ORIGINS_CONFIG  e.g. kits/connectors/bboosty_origins.json (maker, types -> the fit that is the part's joint)
  --torso / --arm library paths without .stl (the arm: one with a Shoulder R fit and a Hand R socket)
Then, before and after the move:
    blender --background --python tests/golden/run.py -- LIB record --squads FILE --golden BEFORE.json
    blender --background --python tests/golden/run.py -- LIB --squads FILE --golden BEFORE.json"""
import sys, os, json, random
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, REPO)
from kb import origin as OG


def opt(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8")); lib = opt("--lib", "D:/Kitbash Library")
    torso, arm, most = opt("--torso"), opt("--arm"), int(opt("--most", 60)); rng = random.Random(7)
    bases = {k: [c["fit"] for c in v if "fit" in c] for k, v in cfg["types"].items()}
    held, packs = [], []
    for d, dn, fs in os.walk(os.path.join(lib, cfg["maker"])):
        dn[:] = sorted(x for x in dn if not x.startswith("_"))
        for f in sorted(fs):
            if not f.endswith(".sockets.json") or not os.path.exists(os.path.join(d, f[:-13] + ".stl")): continue
            try: sc = json.load(open(os.path.join(d, f), encoding="utf-8-sig"))
            except ValueError: continue
            cat = sc.get("category"); rel = os.path.relpath(os.path.join(d, f[:-13]), lib).replace("\\", "/")
            if cat not in bases: continue
            try: OG.move(sc, bases[cat], rel)                       # only what the move would touch
            except OG.Skip: continue
            (packs if "Back" in bases[cat] else held).append((rel, cat))
    pick = lambda L: sorted(rng.sample(L, most)) if len(L) > most else L
    held, packs = pick(held), pick(packs); squads = {}
    for i in range(0, len(held), 2):
        m = [[torso, "Chests", None], [arm, "Arms", "Shoulder R"], [arm, "Arms", "Shoulder L"], [held[i][0], held[i][1], "Hand R"]]
        if i + 1 < len(held): m.append([held[i + 1][0], held[i + 1][1], "Hand L"])
        squads["h%02d" % (i // 2 + 1)] = m
    for i, (rel, cat) in enumerate(packs): squads["p%02d" % (i + 1)] = [[torso, "Chests", None], [rel, cat, "Back"]]
    out = opt("--out", os.path.splitext(sys.argv[1])[0] + "_check.json")
    open(out, "w", encoding="utf-8", newline="\n").write(json.dumps(squads, indent=0))
    print("%s: %d models (%d held parts, %d packs)" % (out, len(squads), len(held), len(packs)))


if __name__ == "__main__":
    main()
