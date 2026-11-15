"""Move a maker's parts onto their joint (notes 101): the STL itself is rewritten so its origin is the joint, and its
fit for that joint becomes none. Blender in the background (only its Python is used), no Claude.

    "Move origins.bat"             list what would move, open the report, answer Y to write (or N: nothing written)
    "Move origins.bat" restore     put back what the last run wrote (its backup), or: restore TASK

    BL kits/connectors/origins.py -- run CONFIG [--lib LIB] [--only TEXT] [--types Arms,Legs] [--yes] [--dry]
    BL kits/connectors/origins.py -- restore [TASK] [--lib LIB] [--yes]
  BL = blender --background --factory-startup --python

CONFIG is the maker's connector file (kits/connectors/marfil.json): its maker, its part types, and for each type the
fit that is the part's own joint (Arms: Shoulder, Legs: Waist, Shoulder Pads: Pad, Knee Pads: Shin).

For every part of those types that has that fit: the file is moved by the fit (kb.origin), so the joint lies on the
origin with the socket's own axes, and the sidecar's sockets, other fits and maker's copies are moved with it; the
part lands exactly where it did. Written per part, originals first into _backups/<task>/before (STL, sidecar, page
preview), each new STL checked against the old one before it replaces it; then the page index. A part with no fit
for its joint, a scale, or anything in its sidecar this doesn't know how to move is left alone and listed.
Run it again after new fits (Seat connectors.bat, Save Correction): only parts whose joint is off the origin move."""
import sys, os, json, time, shutil, hashlib, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, REPO)
from kb import sidecar as SC, origin as OG

LIB = "D:/Kitbash Library"
CHECK = 2e-4              # mm: a rewritten STL's corners must be within this of the old ones moved


def opt(A, n, d=None): return A[A.index(n) + 1] if n in A else d
def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()
def yes(q): return input(q).strip().lstrip(chr(0xfeff)).lower() in ("y", "yes")


def parts(lib, maker, types):
    out = []
    for d, dn, fs in os.walk(os.path.join(lib, maker)):
        dn[:] = sorted(x for x in dn if not x.startswith("_"))
        for f in sorted(fs):
            if not f.endswith(SC.SUFFIX) or not os.path.exists(os.path.join(d, f[:-len(SC.SUFFIX)] + ".stl")): continue
            try: sc = json.load(open(os.path.join(d, f), encoding="utf-8-sig"))
            except ValueError: continue
            if sc.get("category") in types:
                out.append((sc["category"], os.path.relpath(os.path.join(d, f[:-len(SC.SUFFIX)]), lib).replace("\\", "/")))
    return out


def how_far(G):
    M = np.array(G, float).reshape(4, 4)
    return float(np.linalg.norm(M[:3, 3])), math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(M[:3, :3]) - 1) / 2))))


def look(lib, cfg, P, by):
    """what a run would do: [(cat, rel, G or None, what moved)], [(cat, rel, why not)]"""
    todo, left = [], []
    for cat, rel in P:
        sc = json.load(open(lib + "/" + rel + SC.SUFFIX, encoding="utf-8-sig"))
        try: new, G, did = OG.move(sc, cfg["bases"][cat], rel, by)
        except OG.Skip as e: left.append((cat, rel, str(e))); continue
        if G is not None:
            try:
                n = os.path.getsize(lib + "/" + rel + ".stl")
                with open(lib + "/" + rel + ".stl", "rb") as f: f.seek(80); k = int.from_bytes(f.read(4), "little")
                if 84 + 50 * k != n: left.append((cat, rel, "not a plain binary STL")); continue
            except OSError as e: left.append((cat, rel, str(e))); continue
        todo.append((cat, rel, G, did))
    return todo, left


def report(cfg, task, todo, left):
    W = []; w = W.append; nm = lambda rel: rel.split("/", 1)[1]
    files = [t for t in todo if t[2] is not None]
    w("Move origins: %s  (task %s)" % (cfg["maker"], task)); w("")
    w("Will move %d files onto their joint (and %d sidecars where only a maker's copy inside moves)." % (len(files), len(todo) - len(files)))
    done = [l for l in left if l[2] == "done"]; nofit = [l for l in left if l[2] == "no fit for its joint"]
    other = [l for l in left if l not in done and l not in nofit]
    w("Left as they are: %d already on their joint, %d with no fit for their joint, %d this can't move safely." % (len(done), len(nofit), len(other)))
    for cat in cfg["types"]:
        c = [t for t in files if t[0] == cat]
        if not c: w("  %-14s   0 files" % cat); continue
        d = np.array([how_far(t[2]) for t in c])
        w("  %-14s %3d files: origin moves %.1f mm (median; most %.1f), %d of them also turned more than 1 deg" % (
            cat, len(c), np.median(d[:, 0]), d[:, 0].max(), int((d[:, 1] > 1).sum())))
    w(""); w("== No fit for their joint, left (%d): seat them first (Seat connectors.bat, or by eye and Save fit) ==" % len(nofit))
    for cat, rel, why in nofit: w("  %-14s %s" % (cat, nm(rel)))
    if other:
        w(""); w("== Can't be moved safely, left (%d) ==" % len(other))
        for cat, rel, why in other: w("  %-62s %s" % (nm(rel)[:62], why))
    w(""); w("== Files that move (%d): how far the origin goes, and the turn ==" % len(files))
    for cat, rel, G, did in files:
        mm, deg = how_far(G); w("  %-66s %6.1f mm %6.1f deg  %s" % (nm(rel)[:66], mm, deg, ", ".join(did)))
    only = [t for t in todo if t[2] is None]
    if only:
        w(""); w("== Only a copy inside the sidecar moves (%d) ==" % len(only))
        for cat, rel, G, did in only: w("  %-66s %s" % (nm(rel)[:66], ", ".join(did)))
    return "\r\n".join(W) + "\r\n"


def backup(lib, B, rel_file):
    b = B + "/" + rel_file
    if not os.path.exists(b): os.makedirs(os.path.dirname(b), exist_ok=True); shutil.copyfile(lib + "/" + rel_file, b)


def write(lib, T, cfg, todo, by):
    from kb.index import Index
    B = T + "/before"; ip = lib + "/_builder/index.json"; idx = None; note = ""
    try: idx = Index.load(ip); backup(lib, B, "_builder/index.json")
    except (ValueError, OSError) as ex: note = "page index NOT refreshed (%s): run Prepare" % ex
    J = open(T + "/journal.jsonl", "a", encoding="utf-8"); wrote, failed = {}, []
    t0 = time.time()
    for n, (cat, rel, _G, _did) in enumerate(todo):
        scp, stl = lib + "/" + rel + SC.SUFFIX, lib + "/" + rel + ".stl"; begun = []
        try:
            old, style = SC.load(scp)
            new, G, did = OG.move(old, cfg["bases"][cat], rel, by)        # from the file as it is now, not the plan
            bad = [x for x in SC.problems(new) if x not in SC.problems(old)]
            if bad: raise OG.Skip("the moved sidecar would be wrong: %s" % bad[:2])
            e = idx.by_path.get(rel.replace("/", "\\") + ".stl") if idx else None
            prev = "_builder/" + e["prev"] if e and e.get("prev") and "#" not in e["prev"] and os.path.exists(lib + "/_builder/" + e["prev"]) else None
            backup(lib, B, rel + SC.SUFFIX)
            J.write(json.dumps({"rel": rel, "state": "start", "stl": G is not None, "prev": prev if G is not None else None}) + "\n"); J.flush()
            begun = [rel + SC.SUFFIX] + ([rel + ".stl"] + ([prev] if prev else []) if G is not None else [])
            if G is not None:
                backup(lib, B, rel + ".stl")
                tmp = stl + ".moving"; OG.move_stl(stl, tmp, G)
                M = np.array(G, float).reshape(4, 4); P = OG.stl_points(stl); Q = OG.stl_points(tmp)
                err = float(np.abs(P @ M[:3, :3].T + M[:3, 3] - Q).max()) if len(P) == len(Q) and len(P) else 9e9
                if err > CHECK: os.remove(tmp); raise OG.Skip("the rewritten STL is %.5f mm off" % err)
                os.replace(tmp, stl)
            SC.save(scp, new, style)
            if G is not None and prev:
                backup(lib, B, prev); OG.move_preview(lib + "/" + prev, lib + "/" + prev + ".moving", G); os.replace(lib + "/" + prev + ".moving", lib + "/" + prev)
            if e is not None: idx.update_part(e["path"], new)
            wrote[rel] = {"sc": md5(scp), "stl": md5(stl) if G is not None else None, "prev": prev if G is not None else None}
            J.write(json.dumps({"rel": rel, "state": "done"}) + "\n"); J.flush()
        except (OG.Skip, OSError, ValueError, KeyError) as ex:
            failed.append("%s: %s" % (rel, ex))
            for f in begun:                                    # stopped half way: this part back as it was
                if os.path.exists(B + "/" + f): shutil.copyfile(B + "/" + f, lib + "/" + f)
            if begun: J.write(json.dumps({"rel": rel, "state": "undone"}) + "\n"); J.flush()
        if (n + 1) % 50 == 0: print("  %d of %d, %.0f min" % (n + 1, len(todo), (time.time() - t0) / 60), flush=True)
    if idx:
        try: open(ip, "wb").write(idx.dumps()); note = "page index refreshed"
        except OSError as ex: note = "page index NOT refreshed (%s): run Prepare" % ex
    json.dump({"wrote": wrote, "index": md5(ip) if os.path.exists(ip) else None}, open(T + "/written.json", "w", encoding="utf-8"), indent=1)
    return wrote, failed, note


def restore(lib, task, A):
    from kb.index import Index
    root = lib + "/_backups"
    if not task:
        ts = sorted((d for d in os.listdir(root) if d.startswith("origins-") and os.path.exists(root + "/" + d + "/journal.jsonl")),
                    key=lambda d: os.path.getmtime(root + "/" + d + "/journal.jsonl"))
        if not ts: print("no origins.py run to restore"); return
        task = ts[-1]
    T = root + "/" + task; B = T + "/before"
    W = json.load(open(T + "/written.json", encoding="utf-8")) if os.path.exists(T + "/written.json") else {"wrote": {}}
    half = {}                                # started but not finished (the run was stopped): put back whatever is there
    for l in open(T + "/journal.jsonl", encoding="utf-8"):
        j = json.loads(l)
        if j["state"] == "start": half[j["rel"]] = j
        else: half.pop(j["rel"], None)                         # done, or undone by the run itself
    half = {k: v for k, v in half.items() if k not in W["wrote"]}
    print("restore %s: %d parts%s" % (task, len(W["wrote"]), ", and %d the run stopped on" % len(half) if half else ""))
    if "--yes" not in A and not yes("Put them back as they were before that run? [y/N] "): print("nothing changed"); return
    back, changed = [], []
    def put(rel_file):
        if os.path.exists(B + "/" + rel_file): shutil.copyfile(B + "/" + rel_file, lib + "/" + rel_file)
    for rel, m in W["wrote"].items():
        scp, stl = lib + "/" + rel + SC.SUFFIX, lib + "/" + rel + ".stl"
        if not os.path.exists(scp) or md5(scp) != m["sc"] or (m["stl"] and (not os.path.exists(stl) or md5(stl) != m["stl"])):
            changed.append(rel); continue                      # saved since: the file and its sidecar still agree, keep both
        if m["stl"]: put(rel + ".stl")
        put(rel + SC.SUFFIX)
        if m["prev"]: put(m["prev"])
        back.append(rel)
    for rel, j in half.items():
        if j.get("stl"): put(rel + ".stl")
        put(rel + SC.SUFFIX)
        if j.get("prev"): put(j["prev"])
        back.append(rel)
    ip = lib + "/_builder/index.json"; ib = B + "/_builder/index.json"
    if not changed and os.path.exists(ib) and os.path.exists(ip) and md5(ip) == W.get("index"):
        shutil.copyfile(ib, ip); note = "page index put back"
    else:
        try:
            idx = Index.load(ip)
            for rel in back:
                k = rel.replace("/", "\\") + ".stl"
                if k in idx.by_path: idx.update_part(k, SC.load(lib + "/" + rel + SC.SUFFIX)[0])
            open(ip, "wb").write(idx.dumps()); note = "page index refreshed"
        except (ValueError, OSError) as ex: note = "page index NOT refreshed (%s): run Prepare" % ex
    print("put back %d; %d changed since that run, left moved%s; %s" % (len(back), len(changed), (": " + ", ".join(changed[:5])) if changed else "", note))
    with open(T + "/restored.txt", "a", encoding="utf-8") as f: f.write("%s: put back %d, kept %d\n" % (time.strftime("%Y-%m-%d %H:%M"), len(back), len(changed)))


def run(cfgp, A):
    lib = opt(A, "--lib", LIB); cfg = json.load(open(cfgp, encoding="utf-8"))
    types = opt(A, "--types").split(",") if opt(A, "--types") else list(cfg["types"])
    cfg["types"] = {k: v for k, v in cfg["types"].items() if k in types}
    cfg["bases"] = {k: [c["fit"] for c in v if "fit" in c] for k, v in cfg["types"].items()}
    only = opt(A, "--only"); day = time.strftime("%b %d").replace(" 0", " "); by = "origins.py " + day
    task = "origins-" + time.strftime("%Y-%m-%d"); k = 1
    while os.path.exists(lib + "/_backups/" + task): k += 1; task = "origins-%s-%d" % (time.strftime("%Y-%m-%d"), k)
    T = lib + "/_backups/" + task
    P = [(c, r) for c, r in parts(lib, cfg["maker"], list(cfg["types"])) if not only or only in r]
    todo, left = look(lib, cfg, P, by)
    text = report(cfg, task, todo, left)
    print("\n" + text.split("\r\n== ")[0].replace("\r\n", "\n"))
    if not todo: print("nothing to move"); return
    if "--dry" in A: print(text.replace("\r\n", "\n") if "--full" in A else "dry run: nothing written"); return
    os.makedirs(T); open(T + "/report.txt", "wb").write(text.encode("utf-8")); print("The full list: %s/report.txt" % T)
    if "--yes" not in A:
        try: os.startfile(os.path.normpath(T + "/report.txt"))
        except (AttributeError, OSError): pass
        if not yes("Move these %d parts onto their joint? [y/N] " % len(todo)): print("nothing written"); return
    wrote, failed, note = write(lib, T, cfg, todo, by)
    print("moved %d parts (originals in %s\\before); %s" % (len(wrote), T.replace("/", "\\"), note))
    if failed:
        print("!! %d not moved, left as they were:" % len(failed))
        for f in failed[:20]: print("   " + f)
        open(T + "/failed.txt", "w", encoding="utf-8").write("\n".join(failed) + "\n")
    print("To undo: \"Move origins.bat\" restore")


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if not A: print(__doc__)
    elif A[0] == "run": run(A[1], A[2:])
    elif A[0] == "restore": restore(opt(A, "--lib", LIB), A[1] if len(A) > 1 and not A[1].startswith("--") else None, A)
    else: print(__doc__)
