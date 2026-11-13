#!/usr/bin/env python3
"""The PC half of add_creator.py, run through device_bash on Josh's PC (Python 3 standard library; numpy is used for
bounding boxes when it's there). Paths are the device shell's: ~/mnt/d (D:\\) and ~/mnt/Desktop.

  python3 on_pc.py survey SRC TASK [--only GLOB ...] [--skip TEXT ...] [--stage]
      List the STLs under D:\\new cults\\SRC: triangle count, bounding box, md5. Skips presupported copies, macOS
      ._ files and byte-identical duplicates (first path kept). --only keeps paths (relative to SRC) matching a glob,
      --skip drops paths containing a text (case ignored). Prints a short summary and writes
      D:\\Kitbash Library\\_backups\\TASK\\stage\\survey.json. With --stage it also packs, for the container:
      the kept STLs, the Mar Fil reference parts the fits and tests use, the library's state files (_sources.csv,
      _builder\\index.json, _builder\\no_fit.txt, _hidden.txt) and the Part Sockets zip, as stage-NN.tgz
      (<= 250 MB each) in the same folder. Stage those with device_stage_files.

  python3 on_pc.py apply DELIVER_DIR [--check]
      Put a delivery from `add_creator.py build` in place: checks the delivery's md5s, that the library files it
      changes still have the md5 the work was based on, and that no new file is already there; backs those files up
      to _backups\\TASK\\before\\; writes the source sidecars, the maker's files under their library names, the
      library sidecars, previews, _sources.csv rows, index.json, no_fit.txt and _hidden.txt lines; md5-checks
      everything it wrote. --check does every check and writes nothing. Nothing is ever overwritten except the
      four library state files, which are written in place (deletes are off on the PC).
"""
import fnmatch, hashlib, io, json, os, re, struct, sys, tarfile
HOME = os.path.expanduser("~/mnt")
NC = os.path.join(HOME, "d", "new cults")
LIB = os.path.join(HOME, "d", "Kitbash Library")
DESK = os.path.join(HOME, "Desktop")
STATE = ["_sources.csv", "_builder/index.json", "_builder/no_fit.txt", "_hidden.txt"]
REFS = ["Mar Fil - Tacticus/AssaultMarines-V2/Helmet-Heads/Heads/MarFil Assault - Helmet 1",
        "Mar Fil - Tacticus/AssaultMarines-V2/Shoulder Pads/MarFil Assault - Shoulder Pad 1",
        "Mar Fil - Tacticus/AssaultMarines-V2/Chests/MarFil Assault - Torso 1",
        "Mar Fil - Tacticus/AssaultMarines-V2/Legs(JumpPack)/Legs/MarFil Assault - Legs 1A",
        "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 1A R",
        "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 7B R"]
PAGE_BI = os.path.join(DESK, "TIOW Blender bridge", "Squad Builder", "build_index.py")
# presupported copies: a path part or name word like Pres / Presupported / Supported / SUP (not "unsupported")
SUPPORTED = re.compile(r"(^|[^a-z])(pre-?sup(ported)?|pres|supported|sup)([^a-z]|$)", re.I)
CHUNK = 250 * 2 ** 20


def set_roots(nc, lib, page_bi=None):
    """the real folders, for add_creator.py running on the PC itself (no device shell, no ~/mnt)"""
    global NC, LIB, PAGE_BI
    NC, LIB = nc, lib
    if page_bi: PAGE_BI = page_bi


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def stl_info(p):
    size = os.path.getsize(p)
    with open(p, "rb") as f: head = f.read(84)
    n = struct.unpack("<I", head[80:84])[0] if len(head) == 84 else 0
    if size != 84 + 50 * n:
        return {"ascii": True, "tris": None, "bbox": None}
    box = None
    try:
        import numpy as np
        v = np.fromfile(p, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), offset=84)["v"].reshape(-1, 3)
        box = [[round(float(x), 2) for x in v.min(0)], [round(float(x), 2) for x in v.max(0)]]
    except ImportError:
        pass
    return {"ascii": False, "tris": n, "bbox": box}


def survey(args):
    src, task = args[0], args[1]
    only = [a for k, a in zip(args, args[1:]) if k == "--only"]
    skip = [a.lower() for k, a in zip(args, args[1:]) if k == "--skip"]
    root = os.path.join(NC, src)
    assert os.path.isdir(root), "no folder " + root
    files, skipped, other, seen = [], [], {}, {}
    for d, ds, fs in os.walk(root):
        ds.sort()
        for f in sorted(fs):
            p = os.path.join(d, f); rs = os.path.relpath(p, root).replace(os.sep, "/"); rel = src + "/" + rs
            if not f.lower().endswith(".stl"):
                ext = os.path.splitext(f)[1].lower() or "(none)"; other[ext] = other.get(ext, 0) + 1; continue
            if f.startswith("._") or "__MACOSX" in rs: skipped.append([rel, "macOS copy"]); continue
            if any(SUPPORTED.search(x) for x in rs[:-4].split("/")): skipped.append([rel, "presupported"]); continue
            if only and not any(fnmatch.fnmatch(rs, g) for g in only): skipped.append([rel, "not in --only"]); continue
            if any(s in rs.lower() for s in skip): skipped.append([rel, "--skip"]); continue
            m = md5(p)
            if m in seen: skipped.append([rel, "same file as " + seen[m]]); continue
            seen[m] = rel
            files.append(dict(rel=rel, size=os.path.getsize(p), md5=m, **stl_info(p)))
    base = {s: md5(os.path.join(LIB, s)) for s in STATE if os.path.exists(os.path.join(LIB, s))}
    if os.path.exists(PAGE_BI): base["page/build_index.py"] = md5(PAGE_BI)
    K = os.path.join(LIB, "_backups", task, "stage"); os.makedirs(K, exist_ok=True)
    out = {"src": src, "task": task, "files": files, "skipped": skipped, "other": other, "base": base}
    json.dump(out, open(os.path.join(K, "survey.json"), "w"), indent=0)
    # the summary: per folder, kept / skipped, a few names and the typical size
    byf = {}
    for e in files: byf.setdefault(os.path.dirname(e["rel"]), []).append(e)
    for fo in sorted(byf):
        es = byf[fo]; names = [os.path.basename(e["rel"])[:-4] for e in es]
        ext = [max(b - a for a, b in zip(*e["bbox"])) for e in es if e["bbox"]]
        print("%-58s %3d  %s%s  ~%.0f mm" % (fo[len(src) + 1:][-58:] or ".", len(es), ", ".join(names[:4])[:70],
                                           " ..." if len(names) > 4 else "", sorted(ext)[len(ext) // 2] if ext else 0))
    why = {}
    for r, w in skipped: w = "same file" if w.startswith("same file") else w; why[w] = why.get(w, 0) + 1
    print("kept %d STLs (%.0f MB); skipped %s; other files %s; ascii %d" % (
        len(files), sum(e["size"] for e in files) / 2 ** 20, why, other, sum(e["ascii"] for e in files)))
    if "--stage" in args: stage(K, files)


def stage(K, files):
    items = [("new cults/" + e["rel"], os.path.join(NC, e["rel"])) for e in files]
    for r in REFS:
        for ext in (".stl", ".sockets.json"): items.append(("Kitbash Library/" + r + ext, os.path.join(LIB, r + ext)))
    for s in STATE:
        if os.path.exists(os.path.join(LIB, s)): items.append(("Kitbash Library/" + s, os.path.join(LIB, s)))
    zips = sorted((tuple(int(x) for x in m.group(1).split(".")), f) for f in os.listdir(DESK)   # the add-on, not its wiki
                  for m in [re.match(r"part_sockets_(\d+(?:\.\d+)*)\.zip$", f)] if m)
    if zips: items.append(("Desktop/" + zips[-1][1], os.path.join(DESK, zips[-1][1])))
    items.append(("stage/survey.json", os.path.join(K, "survey.json")))
    for f in os.listdir(K):
        if re.match(r"stage-\d+\.tgz$", f): sys.exit("stage files already in " + K + ": use a new TASK name")
    n, size, t, made = 0, 0, None, []
    for arc, p in items:
        s = os.path.getsize(p)
        if t is None or size + s > CHUNK:
            if t: t.close()
            n += 1; size = 0; made.append(os.path.join(K, "stage-%02d.tgz" % n)); t = tarfile.open(made[-1], "x:gz")
        t.add(p, arcname=arc); size += s
    t.close()
    print("staged %d files in %d archive(s):" % (len(items), len(made)))
    for m in made: print("  ~/mnt/d/" + os.path.relpath(m, os.path.join(HOME, "d")).replace(os.sep, "/"), "%.0f MB" % (os.path.getsize(m) / 2 ** 20))


def members(tgz):
    with tarfile.open(tgz, "r:gz") as t:
        for m in t.getmembers():
            if m.isfile():
                assert not m.name.startswith("/") and ".." not in m.name.split("/"), m.name
                yield m.name, t.extractfile(m).read()


def write_new(p, data):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "xb") as f: f.write(data)


def put(p, data):          # in place: the PC's shell can't unlink (deletes are off)
    with open(p, "r+b") as f: f.write(data); f.truncate()


def apply(args):
    D = args[0]; check = "--check" in args
    M = json.load(open(os.path.join(D, "manifest.json")))
    K = os.path.join(LIB, "_backups", M["task"])
    for f, parts in M.get("split", {}).items():       # files sent in parts (device_commit_files' size limit)
        if not os.path.exists(os.path.join(D, f)):
            write_new(os.path.join(D, f), b"".join(open(os.path.join(D, q), "rb").read() for q in parts))
    bad = [f for f, m in M["files"].items() if md5(os.path.join(D, f)) != m]
    if bad: sys.exit("delivery files damaged: %s" % bad)
    changed = [s for s, m in M["base"].items() if md5(os.path.join(LIB, s)) != m]
    if changed: sys.exit("changed since the work was staged (re-stage and rebuild): %s" % changed)
    src_sc = list(members(os.path.join(D, "source_sidecars.tgz")))
    lib_sc = list(members(os.path.join(D, "library_sidecars.tgz")))
    prev = list(members(os.path.join(D, "previews.tgz")))
    problems = []
    for src, lib, m in M["copies"]:
        if not os.path.exists(os.path.join(NC, src)): problems.append("missing source " + src)
        elif md5(os.path.join(NC, src)) != m: problems.append("source changed " + src)
        if os.path.exists(os.path.join(LIB, lib)): problems.append("already in the library " + lib)
    for name, _ in lib_sc:
        if os.path.exists(os.path.join(LIB, name)): problems.append("already in the library " + name)
    keep_src = []
    for name, data in src_sc:
        p = os.path.join(NC, name)
        if not os.path.exists(p): keep_src.append((name, data))
        elif open(p, "rb").read() != data: problems.append("a different source sidecar is there " + name)
    new_prev = [(n, d) for n, d in prev if not os.path.exists(os.path.join(LIB, "_builder", n))]
    s = open(os.path.join(LIB, "_sources.csv"), "rb").read(); rows = open(os.path.join(D, "rows.csv"), "rb").read()
    if not (s.endswith(b"\r\n") and rows.endswith(b"\r\n")): problems.append("_sources.csv or rows.csv doesn't end in CRLF")
    if problems: sys.exit("not applied:\n  " + "\n  ".join(problems[:20]) + ("\n  ..." if len(problems) > 20 else ""))
    print("ok to apply: %d maker files to library names, %d library sidecars, %d source sidecars (%d already there), "
          "%d previews, %d _sources.csv rows, %d no_fit lines, %d hidden lines" % (
              len(M["copies"]), len(lib_sc), len(keep_src), len(src_sc) - len(keep_src), len(new_prev),
              rows.count(b"\r\n"), len(M["nofit"]), len(M["hide"])))
    if check: return
    os.makedirs(os.path.join(K, "before"), exist_ok=True)
    for st in M["base"]:
        b = os.path.join(K, "before", st.replace("/", "__"))
        if not os.path.exists(b): write_new(b, open(os.path.join(LIB, st), "rb").read())
    for name, data in keep_src: write_new(os.path.join(NC, name), data)
    for src, lib, m in M["copies"]: write_new(os.path.join(LIB, lib), open(os.path.join(NC, src), "rb").read())
    for name, data in lib_sc: write_new(os.path.join(LIB, name), data)
    for name, data in new_prev: write_new(os.path.join(LIB, "_builder", name), data)
    put(os.path.join(LIB, "_sources.csv"), s + rows)
    put(os.path.join(LIB, "_builder/index.json"), open(os.path.join(D, "index.json"), "rb").read())
    for st, lines in (("_builder/no_fit.txt", M["nofit"]), ("_hidden.txt", M["hide"])):
        if not lines: continue
        p = os.path.join(LIB, st); t = open(p, "rb").read(); nl = b"\r\n" if b"\r\n" in t else b"\n"
        add = nl.join(x.encode("utf-8") for x in lines) + nl
        put(p, t + (b"" if not t or t.endswith(nl) else nl) + add)
    # check everything written
    bad = [lib for src, lib, m in M["copies"] if md5(os.path.join(LIB, lib)) != m]
    bad += [n for n, d in lib_sc if open(os.path.join(LIB, n), "rb").read() != d]
    bad += [n for n, d in src_sc if open(os.path.join(NC, n), "rb").read() != d]
    bad += [n for n, d in prev if open(os.path.join(LIB, "_builder", n), "rb").read() != d]
    if md5(os.path.join(LIB, "_builder/index.json")) != M["files"]["index.json"]: bad.append("index.json")
    if not open(os.path.join(LIB, "_sources.csv"), "rb").read().endswith(rows): bad.append("_sources.csv")
    idx = json.load(open(os.path.join(LIB, "_builder/index.json"), encoding="utf-8"))
    nop = sum(not os.path.exists(os.path.join(LIB, "_builder", e["prev"])) for e in idx["parts"] if e.get("prev"))
    print("applied; %s; index %d parts, %d previews missing" % ("all md5s match" if not bad else "MISMATCH: %s" % bad[:10], len(idx["parts"]), nop))
    print("now: " + ", ".join("%s %s" % (st, md5(os.path.join(LIB, st))[:8]) for st in M["base"]))


if __name__ == "__main__":
    cmd, rest = sys.argv[1], sys.argv[2:]
    {"survey": survey, "apply": apply}[cmd](rest)
