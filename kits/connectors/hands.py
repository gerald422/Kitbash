"""Find a maker's weapon hand designs (notes 104 / 105): no cuts, dry runs only, nothing written to the library.

    python kits/connectors/hands.py CONFIG [--lib LIB] [--rounds 20] [--resume _backups/hands-DATE]

CONFIG (e.g. kits/connectors/marfil_hands.json): maker, blends, the arm-side cut ("blend", "spot"), the arm it is on
("on", with its "socket"), the first example ("first") and the types. A weapon that comes with its hand mates at the
wrist; its side is taken from one example placed on the arm by its library fit (seat.py "placed" connector). Each
round: the example's side is searched over every weapon not yet covered (seat.py run --dry --list), the sure matches
(the same hand sculpt) join its group, and the next example is a fitted right-hand weapon from the kit with the most
left. Stops when nothing is left to try. Writes _backups/hands-DATE/summary.json and report.txt: each hand design
(its example and group, and how far the group's new fits are from their library fits) and what no example covers.
Each round's dry run stays in _backups/connectors-*: `seat.py write TASK --sure` writes a group once Josh agrees."""
import sys, os, json, time, subprocess, re, collections, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, REPO)
from kb import sidecar as SC, origin as OG
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
HANDLESS = ("no hand", "handless", "hand-less", "without hand")


def opt(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def scan(lib, maker, types):
    out = {}
    for d, dn, fs in os.walk(os.path.join(lib, maker)):
        dn[:] = sorted(x for x in dn if not x.startswith("_"))
        for f in sorted(fs):
            if not f.endswith(SC.SUFFIX) or not os.path.exists(os.path.join(d, f[:-len(SC.SUFFIX)] + ".stl")): continue
            try: sc = json.load(open(os.path.join(d, f), encoding="utf-8-sig"))
            except ValueError: continue
            name = f[:-len(SC.SUFFIX)]
            if sc.get("category") in types and not any(w in name.lower() for w in HANDLESS):
                out[os.path.relpath(os.path.join(d, name), lib).replace("\\", "/")] = OG.with_joint_fit(sc)
    return out


def kit(rel): return rel.split("/")[1]


def nxt(P, left, tried, base="Hand"):
    """the next example: one fitted for base (a right-hand fit first, else a left one: seat.py mirrors it) from the kit
    with the most left"""
    fits = lambda x: P[x].get("fits") or {}
    cands = [x for x in left if x not in tried and (base in fits(x) or base + " R" in fits(x))] or \
            [x for x in left if x not in tried and base + " L" in fits(x)]
    if not cands: return None
    big = collections.Counter(kit(x) for x in cands).most_common(1)[0][0]
    return sorted((x for x in cands if kit(x) == big),
                  key=lambda x: (not any(e in (base, base + " R", base + " L") for e in P[x].get("exact") or []), x))[0]


def main():
    cfgp = sys.argv[1]; lib = opt("--lib", "D:/Kitbash Library"); cfg = json.load(open(cfgp, encoding="utf-8"))
    base, label = cfg.get("fit", "Hand"), cfg.get("label", "hands")
    P = scan(lib, cfg["maker"], cfg["types"]); left = set(P); covered = {}; rounds = []; tried = set()
    if opt("--resume"):        # carry on a run that hit --rounds: its summary's rounds and what was left
        T = opt("--resume").rstrip("/\\"); s = json.load(open(T + "/summary.json", encoding="utf-8")); rounds = s["rounds"]
        left = set(s["left"]) & set(P); tried = {r["example"] for r in rounds}
        for r in rounds:
            for x in r["group"] + [r["example"]]: covered[x] = r["round"]
        ex = nxt(P, left, tried, base)
    else:
        T = lib + "/_backups/%s-%s" % (label, time.strftime("%Y-%m-%d")); k = 1
        while os.path.exists(T): k += 1; T = lib + "/_backups/%s-%s-%d" % (label, time.strftime("%Y-%m-%d"), k)
        os.makedirs(T); ex = cfg["first"]
    print("%d parts (%s)" % (len(P), ", ".join("%s %d" % x for x in collections.Counter(kit(r) for r in P).most_common())), flush=True)
    for rnd in range(len(rounds), len(rounds) + int(opt("--rounds", 20))):
        if ex is None: break
        tried.add(ex); left.discard(ex)
        con = {"name": "%s %d" % (label.rstrip("s"), rnd + 1), "on": cfg["on"], "socket": cfg["socket"], "placed": ex, "ref": ex, "fit": base}
        con.update({k: cfg[k] for k in ("blend", "spot", "spot_mm", "gap") if k in cfg})   # no "spot": the "on" part's own surface
        rc = {"maker": cfg["maker"], "blends": cfg["blends"], "types": {t: [con] for t in cfg["types"]}}
        json.dump(rc, open(T + "/round%02d.json" % (rnd + 1), "w", encoding="utf-8"), indent=1)
        open(T + "/round%02d.txt" % (rnd + 1), "w", encoding="utf-8").write("\n".join(sorted(left)))
        t0 = time.time()
        out = subprocess.run([BLENDER, "--background", "--factory-startup", "--python", os.path.join(HERE, "seat.py"), "--", "run",
                              T + "/round%02d.json" % (rnd + 1), "--lib", lib, "--list", T + "/round%02d.txt" % (rnd + 1), "--dry"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL).stdout
        m = re.search(r"(connectors-\d{4}-\d\d-\d\d(?:-\d+)?): reading", out)
        if m and "STOPPED" in out and re.search(r"only \d+ triangles", out):     # placed by its fit it doesn't touch the
            rounds.append({"round": rnd + 1, "example": ex, "task": m.group(1), "group": [], "far": [], "no_side": True,  # spot
                           "moved_med": None, "turn_med": None, "moved_max": None, "kits": {}, "secs": round(time.time() - t0)})
            print("round %2d  %-58s no side: placed by its fit it doesn't touch the spot" % (rnd + 1, ex.split("/")[-1][:58]), flush=True)
            json.dump({"config": cfg, "rounds": rounds, "left": sorted(left)}, open(T + "/summary.json", "w", encoding="utf-8"), indent=1)
            ex = nxt(P, left, tried, base); continue
        if not m or "STOPPED" in out: print(out[-1500:]); break
        task = m.group(1); plan = json.load(open(lib + "/_backups/" + task + "/plan.json", encoding="utf-8"))
        sure = [p for p in plan if p.get("fit") and p["fit"]["level"] == "sure"]
        mv = [(p["fit"].get("moved_mm"), p["fit"].get("turn_deg")) for p in sure if p["fit"].get("had")]
        far = [p["rel"] for p in sure if p["fit"].get("had") and (p["fit"]["moved_mm"] > 2 or p["fit"]["turn_deg"] > 10)]
        r = {"round": rnd + 1, "example": ex, "task": task, "group": [p["rel"] for p in sure], "far": far,
             "moved_med": round(st.median([a for a, b in mv]), 2) if mv else None, "turn_med": round(st.median([b for a, b in mv]), 1) if mv else None,
             "moved_max": max([a for a, b in mv]) if mv else None, "kits": dict(collections.Counter(kit(p["rel"]) for p in sure)), "secs": round(time.time() - t0)}
        rounds.append(r)
        for p in sure: covered[p["rel"]] = rnd + 1; left.discard(p["rel"])
        covered[ex] = rnd + 1
        print("round %2d  %-58s +%3d (%s)  moved med %s mm / %s deg, %d far  [%d left, %d s]" % (rnd + 1, ex.split("/")[-1][:58], len(sure),
              ", ".join("%s %d" % x for x in r["kits"].items()), r["moved_med"], r["turn_med"], len(far), len(left), r["secs"]), flush=True)
        json.dump({"config": cfg, "rounds": rounds, "left": sorted(left)}, open(T + "/summary.json", "w", encoding="utf-8"), indent=1)
        ex = nxt(P, left, tried, base)
    W = ["Designs at the %s joint: %s (%s)" % (base, cfg["maker"], os.path.basename(T)), "",
         "%d parts; %d in a group of 2 or more, %d alone (their own hand, or the search found no match), %d with no fit to try." % (
             len(P), sum(len(r["group"]) + 1 for r in rounds if r["group"]), sum(1 for r in rounds if not r["group"]), len(left)), ""]
    for r in sorted(rounds, key=lambda r: -len(r["group"])):
        W.append("%3d + 1  %s   (%s)   new fits from the library: %s mm / %s deg median, %s mm most%s   [%s]" % (
            len(r["group"]), r["example"].split("/", 1)[1], ", ".join("%s %d" % x for x in r["kits"].items()) or "-", r["moved_med"], r["turn_med"],
            r["moved_max"], (", %d over 2 mm / 10 deg" % len(r["far"])) if r["far"] else "", r["task"]))
    if left:
        W += ["", "Not covered (no fit to take an example from, or never matched):"] + ["  " + x.split("/", 1)[1] for x in sorted(left)]
    open(T + "/report.txt", "w", encoding="utf-8").write("\n".join(W) + "\n"); print("\n".join(W[:4])); print("report:", T + "/report.txt")


if __name__ == "__main__":
    main()
