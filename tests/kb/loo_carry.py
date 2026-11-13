"""Leave-one-out check of kb.carry on the library: is what it keeps right, and how much does it keep?

    python tests/kb/loo_carry.py LIBRARY [PER_MAKER=12] [TYPES=Arms,Legs,Chests] [OUT.json]
    (a Python with numpy; scipy makes it about ten times faster. Read only; about 5 s a part with scipy.)

For a sample of fitted arms, legs and socketed torsos: the part's own sidecar is hidden, kb.carry.like carries its
joints from the other fitted parts of its folder, and the result is compared with what the library has ("right" =
within 0.5 mm and 3 deg). Prints, per type and per maker, how many joints were kept / right / dropped, and for legs
the sockets that came with the waist. The sidecars are read from this clone's library/, the STLs from LIBRARY.
"""
import sys, os, json, time, random, collections
import numpy as np
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, REPO)
from kb import carry

A = sys.argv[1:]
if not A: sys.exit(__doc__)
LIB = A[0]; NPER = int(A[1]) if len(A) > 1 else 12; CATS = (A[2] if len(A) > 2 else "Arms,Legs,Chests").split(",")
random.seed(11)
ok = lambda mm, dg: mm <= 0.5 and dg <= 3
parts = collections.defaultdict(list)
for d, _, fs in os.walk(os.path.join(REPO, "library")):
    for f in fs:
        if not f.endswith(".sockets.json"): continue
        rel = os.path.relpath(os.path.join(d, f), os.path.join(REPO, "library")).replace("\\", "/")
        sc = json.load(open(os.path.join(d, f), encoding="utf-8-sig")); cat = sc.get("category")
        if cat in CATS and carry.joints(cat, sc) and not sc.get("upright"): parts[cat].append((rel, sc))
stl = lambda rel: os.path.join(LIB, rel[:-13] + ".stl")
rows, socks = [], []
for cat in CATS:
    bym = collections.defaultdict(list)
    for rel, sc in parts[cat]: bym[rel.split("/")[0]].append((rel, sc))
    for maker in sorted(bym, key=lambda m: -len(bym[m]))[:5]:
        for rel, sc in random.sample(bym[maker], min(NPER, len(bym[maker]))):
            t0 = time.time(); J = carry.joints(cat, sc)
            refs = [carry.Ref(os.path.basename(r)[:-13], s, stl(r)) for r, s in bym[maker] if os.path.dirname(r) == os.path.dirname(rel) and r != rel]
            if not os.path.isfile(stl(rel)): continue
            got = carry.like(cat, carry.Shape(stl(rel), sc.get("scale", 1.0)), refs, mirror=False)
            mine = dict(got["fits"]); mine.update({s["type"]: s["matrix"] for s in got["sockets"] if s["type"] in carry.TORSO and cat == "Chests"})
            line = []
            for name, (kind, T) in J.items():
                how = got["how"].get(name)
                if name in mine:
                    X = np.array(mine[name]).reshape(4, 4); mm = float(np.linalg.norm(carry.point(kind, X) - carry.point(kind, T))); dg = carry.ang(X, T)
                    rows.append((cat, maker, how["mode"], "kept", mm, dg, how["match"], how["whole"])); line.append("%s[%s] %.2fmm %.1fdeg (match %.2f, whole %.2f)" % (name, how["mode"], mm, dg, how["match"], how["whole"]))
                else:
                    rows.append((cat, maker, how["mode"] if how else "-", "dropped", None, None, how["match"] if how else None, how["whole"] if how else None)); line.append("%s dropped" % name)
            if cat == "Legs" and got["fits"]:
                true = collections.defaultdict(list)
                for s in sc.get("sockets") or []: true[s["type"]].append(np.array(s["matrix"]).reshape(4, 4))
                for s in got["sockets"]:
                    X = np.array(s["matrix"]).reshape(4, 4)
                    if true.get(s["type"]):
                        T = min(true[s["type"]], key=lambda T: np.linalg.norm(T[:3, 3] - X[:3, 3]))
                        socks.append((maker, s["type"], float(np.linalg.norm(T[:3, 3] - X[:3, 3])), carry.ang(X, T), max(h["match"] for h in got["how"].values())))
            print("%-6s %-26s %-40s %s (%.0f s)" % (cat, maker[:26], os.path.basename(rel)[:-13][:40], "  ".join(line), time.time() - t0), flush=True)
print("\n=== kb.carry, leave-one-out: kept / right (within 0.5 mm and 3 deg) / dropped ===")
for cat in CATS:
    R = [r for r in rows if r[0] == cat]
    if not R: continue
    K = [r for r in R if r[3] == "kept"]
    print("%-6s %3d joints: kept %d, right %d, dropped %d%s" % (cat, len(R), len(K), sum(ok(r[4], r[5]) for r in K), len(R) - len(K),
          "" if not K else "; kept ones: position median %.2f, worst %.2f mm, turn worst %.1f deg" % (np.median([r[4] for r in K]), max(r[4] for r in K), max(r[5] for r in K))))
    by = collections.defaultdict(list)
    for r in R: by[(r[1], r[2])].append(r)
    for (m, mode), X in sorted(by.items()):
        k = [r for r in X if r[3] == "kept"]
        print("     %-30s %-5s %3d joints: kept %2d, right %2d, dropped %2d" % (m[:30], mode, len(X), len(k), sum(ok(r[4], r[5]) for r in k), len(X) - len(k)))
if socks:
    print("legs' sockets that came with the waist (against the library's):")
    by = collections.defaultdict(list)
    for m, t, mm, dg, mt in socks: by[t].append((mm, dg))
    for t, X in sorted(by.items()): print("     %-11s %3d: position median %.2f, 90%% %.2f, worst %.2f mm; turn median %.1f, worst %.1f deg" % (
        t, len(X), np.median([x[0] for x in X]), np.quantile([x[0] for x in X], 0.9), max(x[0] for x in X), np.median([x[1] for x in X]), max(x[1] for x in X)))
for cat in CATS:                      # would a tighter gate have kept only right ones?
    K = [r for r in rows if r[0] == cat and r[3] == "kept" and r[2] != "same"]
    for g in (0.06, 0.08, 0.10):
        k = [r for r in K if r[6] <= g]
        if K and len(k) < len(K): print("%-6s (not 'same') region match <= %.2f: keeps %d of %d, right %d" % (cat, g, len(k), len(K), sum(ok(r[4], r[5]) for r in k)))
    if cat == "Legs" and socks:
        for g in (0.06, 0.08, 0.12):
            k = [x for x in socks if x[4] <= g and x[1] != "Base"]
            if k: print("       belt sockets where the waist matched <= %.2f: %d, position 90%% %.2f, worst %.2f mm; turn 90%% %.1f, worst %.1f deg" % (
                g, len(k), np.quantile([x[2] for x in k], 0.9), max(x[2] for x in k), np.quantile([x[3] for x in k], 0.9), max(x[3] for x in k)))
if len(A) > 3: json.dump([list(r) for r in rows], open(A[3], "w"))
