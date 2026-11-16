"""RETIRED Nov 16 (docs/PLAN.md): not to be used for placing. It anchors each group on an example's old library fit and
takes "whatever touches" as the connector, so it splits parts by sculpt; Josh replaced it with cuts of the mating surface.
Kept only as the record of the Nov 15 runs (notes 105, 107, 108) and for `write` / restore of those.

Find a maker's weapon hand designs (notes 104 / 105): no cuts, dry runs only, nothing written to the library.

    python kits/connectors/hands.py CONFIG [--lib LIB] [--rounds 20] [--quiet N] [--workers N] [--no-unfitted] [--resume _backups/hands-DATE]
    python kits/connectors/hands.py write _backups/hands-DATE [--lib LIB] [--near 2]     writes every group of that run

CONFIG (e.g. kits/connectors/marfil_hands.json): maker, blends, the arm-side cut ("blend", "spot"), the arm it is on
("on", with its "socket"), the first example ("first") and the types. A weapon that comes with its hand mates at the
wrist; its side is taken from one example placed on the arm by its library fit (seat.py "placed" connector). Each
round: the example's side is searched over every weapon not yet covered (seat.py run --dry --list), the sure matches
(the same hand sculpt) join its group, and the next example is a fitted right-hand weapon from the kit with the most
left. Stops when nothing is left to try. Writes _backups/hands-DATE/summary.json and report.txt: each hand design
(its example and group, and how far the group's new fits are from their library fits) and what no example covers.
Each round's dry run stays in _backups/connectors-*: `seat.py write TASK --sure` writes a group once Josh agrees.
Other makers (notes 108): no "blend" / "spot" (the "on" part's own surface within "spot_mm" of its socket is the spot,
as for backpacks, notes 107), "on" may be a part of another folder, "first" may be left out (the first example is
then picked like the later ones), "skip" lists folder names left out. --quiet N stops after N rounds in a row that
matched nothing (a long tail of one-off hands). A weapon that has a fit is checked where that fit puts the example's
side (and its half turns), not searched from scratch (seat.py at_fit; config "near_first": false for the full search,
as Mar Fil's runs were). Those with no fit are searched in full afterwards, only with the designs that formed a group
(--no-unfitted leaves them out). `write DIR` runs `seat.py write TASK --sure --near MM --yes` for each
round of that run that has a group and was not written yet (backups in each task's `before`; `seat.py restore TASK`
undoes one), and lists what it left as it was in DIR/written.txt."""
import sys, os, json, time, subprocess, re, collections, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, REPO)
from kb import sidecar as SC, origin as OG
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
HANDLESS = ("no hand", "handless", "hand-less", "without hand")
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")   # one thread a worker: seat.py runs a dozen


def opt(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def scan(lib, maker, types, skip=()):
    out = {}
    for d, dn, fs in os.walk(os.path.join(lib, maker)):
        dn[:] = sorted(x for x in dn if not x.startswith("_") and not any(w.lower() in x.lower() for w in skip))
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


def write_run(T, lib, near):
    """write each group of a finished run: the sure fits within `near` mm / 10 deg of the old fit (seat.py write)"""
    s = json.load(open(T + "/summary.json", encoding="utf-8")); W = []; total = 0
    for r in s["rounds"]:
        if not r.get("group"): continue
        D = lib + "/_backups/" + r["task"]; ex = r["example"].split("/")[-1]
        if os.path.exists(D + "/written.json"): W.append("%s  %s: written already" % (r["task"], ex)); continue
        out = subprocess.run([BLENDER, "--background", "--factory-startup", "--python", os.path.join(HERE, "seat.py"), "--", "write", r["task"],
                              "--lib", lib, "--sure", "--near", str(near), "--yes"], capture_output=True, text=True, encoding="utf-8",
                             errors="replace", stdin=subprocess.DEVNULL).stdout
        m = re.search(r"wrote (\d+) sidecars", out); n = int(m.group(1)) if m else 0; total += n
        far = open(D + "/left_far.txt", encoding="utf-8").read().splitlines() if os.path.exists(D + "/left_far.txt") else []
        line = "%s  %-56s group %3d, wrote %3d" % (r["task"], ex[:56], len(r["group"]), n)
        if far: line += ", %d left as they were (over %g mm / 10 deg)" % (len(far), near)
        if not m: line += "  !! not written: " + " | ".join(out[-300:].splitlines())
        print(line, flush=True); W.append(line); W += ["      far: " + x for x in far]
    W.append("wrote %d fits" % total); print(W[-1])
    with open(T + "/written.txt", "a", encoding="utf-8") as f: f.write(time.strftime("%Y-%m-%d %H:%M") + "\n" + "\n".join(W) + "\n\n")


def main():
    if sys.argv[1] == "write": return write_run(sys.argv[2].rstrip("/\\"), opt("--lib", "D:/Kitbash Library"), float(opt("--near", 2)))
    cfgp = sys.argv[1]; lib = opt("--lib", "D:/Kitbash Library"); cfg = json.load(open(cfgp, encoding="utf-8"))
    base, label = cfg.get("fit", "Hand"), cfg.get("label", "hands")
    P = scan(lib, cfg["maker"], cfg["types"], cfg.get("skip", ())); left = set(P); rounds = []; tried = set()
    fitted = lambda x: any(k in (P[x].get("fits") or {}) for k in (base, base + " R", base + " L"))
    if opt("--resume"):        # carry on a run that hit --rounds: its summary's rounds and what was left
        T = opt("--resume").rstrip("/\\"); s = json.load(open(T + "/summary.json", encoding="utf-8")); rounds = s["rounds"]
        left = set(s["left"]) & set(P); tried = {r["example"] for r in rounds}
        ex = nxt(P, left, tried, base)
    else:
        T = lib + "/_backups/%s-%s" % (label, time.strftime("%Y-%m-%d")); k = 1
        while os.path.exists(T): k += 1; T = lib + "/_backups/%s-%s-%d" % (label, time.strftime("%Y-%m-%d"), k)
        os.makedirs(T); ex = cfg.get("first") or nxt(P, left, tried, base)
    print("%d parts (%s); %d have no fit" % (len(P), ", ".join("%s %d" % x for x in collections.Counter(kit(r) for r in P).most_common()),
                                           sum(1 for x in P if not fitted(x))), flush=True)
    save = lambda: json.dump({"config": cfg, "rounds": rounds, "left": sorted(left)}, open(T + "/summary.json", "w", encoding="utf-8"), indent=1)

    def one(ex, todo, unfitted=False):
        """a dry seat.py run of example ex's side over todo; the round's record, or None when the run failed"""
        n = len(rounds) + 1; t0 = time.time(); todo = sorted(todo)
        r = {"round": n, "example": ex, "task": None, "group": [], "far": [], "moved_med": None, "turn_med": None, "moved_max": None, "kits": {}}
        if unfitted: r["unfitted"] = True
        if todo:
            con = {"name": "%s %d" % (label.rstrip("s"), n), "on": cfg["on"], "socket": cfg["socket"], "placed": ex, "ref": ex, "fit": base}
            con.update({k: cfg[k] for k in ("blend", "spot", "spot_mm", "gap") if k in cfg})   # no "spot": the "on" part's own surface
            rc = {"maker": cfg["maker"], "blends": cfg.get("blends", ""), "near_first": cfg.get("near_first", True),   # a fitted part is
                  "types": {t: [con] for t in cfg["types"]}}                                    # checked at its fit, not searched (seat.at_fit)
            json.dump(rc, open(T + "/round%02d.json" % n, "w", encoding="utf-8"), indent=1)
            open(T + "/round%02d.txt" % n, "w", encoding="utf-8").write("\n".join(todo))
            out = subprocess.run([BLENDER, "--background", "--factory-startup", "--python", os.path.join(HERE, "seat.py"), "--", "run",
                                  T + "/round%02d.json" % n, "--lib", lib, "--list", T + "/round%02d.txt" % n, "--dry"] +
                                 (["--workers", opt("--workers")] if opt("--workers") else []), env=ENV,
                                 capture_output=True, text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL).stdout
            m = re.search(r"(connectors-\d{4}-\d\d-\d\d(?:-\d+)?): reading", out)
            if m and "STOPPED" in out and re.search(r"only \d+ triangles", out):     # placed by its fit it doesn't touch the spot
                r.update(task=m.group(1), no_side=True, secs=round(time.time() - t0))
                print("round %2d  %-58s no side: placed by its fit it doesn't touch the spot" % (n, ex.split("/")[-1][:58]), flush=True); return r
            if not m or "STOPPED" in out: print(out[-1500:]); return None
            plan = json.load(open(lib + "/_backups/" + m.group(1) + "/plan.json", encoding="utf-8"))
            sure = [p for p in plan if p.get("fit") and p["fit"]["level"] == "sure"]
            mv = [(p["fit"].get("moved_mm"), p["fit"].get("turn_deg")) for p in sure if p["fit"].get("had")]
            r.update(task=m.group(1), group=[p["rel"] for p in sure], kits=dict(collections.Counter(kit(p["rel"]) for p in sure)),
                     far=[p["rel"] for p in sure if p["fit"].get("had") and (p["fit"]["moved_mm"] > 2 or p["fit"]["turn_deg"] > 10)],
                     moved_med=round(st.median([a for a, b in mv]), 2) if mv else None, turn_med=round(st.median([b for a, b in mv]), 1) if mv else None,
                     moved_max=max([a for a, b in mv]) if mv else None)
        r["secs"] = round(time.time() - t0)
        print("round %2d  %-58s +%3d (%s)  moved med %s mm / %s deg, %d far  [%s, %d s]" % (n, ex.split("/")[-1][:58], len(r["group"]),
              ", ".join("%s %d" % x for x in r["kits"].items()), r["moved_med"], r["turn_med"], len(r["far"]),
              "of %d with no fit" % len(todo) if unfitted else "%d left" % (len(left) - len(r["group"])), r["secs"]), flush=True)
        return r

    # 1. the designs, among the parts that have a fit (each checked at its own fit: seconds a part)
    quiet = int(opt("--quiet", 0))
    for _ in range(int(opt("--rounds", 20))):
        if ex is None: break
        own = [r for r in rounds if not r.get("unfitted")]
        if quiet and len(own) >= quiet and not any(r["group"] for r in own[-quiet:]):
            print("stopped: the last %d examples matched nothing else" % quiet, flush=True); break
        tried.add(ex); left.discard(ex)
        r = one(ex, [x for x in left if fitted(x)] if cfg.get("near_first", True) else left)
        if r is None: break
        rounds.append(r); left.difference_update(r["group"]); save(); ex = nxt(P, left, tried, base)
    # 2. the parts with no fit: searched in full (a minute a part), so only with the designs that formed a group, biggest
    #    first. (With "near_first": false every round searched them already, as Mar Fil's runs did.)
    if cfg.get("near_first", True) and "--no-unfitted" not in sys.argv:
        did = {r["example"] for r in rounds if r.get("unfitted")}
        for r0 in sorted((r for r in rounds if r["group"] and not r.get("unfitted")), key=lambda r: -len(r["group"])):
            unf = [x for x in left if not fitted(x)]
            if not unf: break
            if r0["example"] in did: continue
            r = one(r0["example"], unf, unfitted=True)
            if r is None: break
            rounds.append(r); left.difference_update(r["group"]); save()
    grouped = {x for r in rounds for x in r["group"]} | {r["example"] for r in rounds if r["group"]}
    W = ["Designs at the %s joint: %s (%s)" % (base, cfg["maker"], os.path.basename(T)), "",
         "%d parts; %d in a group of 2 or more, %d alone (their own hand, or the search found no match), %d not covered." % (
             len(P), len(grouped), len({r["example"] for r in rounds} - grouped), len(left)), ""]
    for r in sorted(rounds, key=lambda r: -len(r["group"])):
        if r.get("unfitted") and not r["group"]: continue
        W.append("%3d + %s  %s   (%s)   new fits from the library: %s mm / %s deg median, %s mm most%s   [%s]" % (
            len(r["group"]), "parts that had no fit, like" if r.get("unfitted") else "1", r["example"].split("/", 1)[1],
            ", ".join("%s %d" % x for x in r["kits"].items()) or "-", r["moved_med"], r["turn_med"],
            r["moved_max"], (", %d over 2 mm / 10 deg" % len(r["far"])) if r["far"] else "", r["task"]))
    if left:
        W += ["", "Not covered (no fit to take an example from, or never matched):"] + ["  " + x.split("/", 1)[1] for x in sorted(left)]
    open(T + "/report.txt", "w", encoding="utf-8").write("\n".join(W) + "\n"); print("\n".join(W[:4])); print("report:", T + "/report.txt")


if __name__ == "__main__":
    main()
