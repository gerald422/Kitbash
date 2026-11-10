#!/usr/bin/env python3
"""The PC half of every task, standard library only. Runs in the device shell (~/mnt/...) or in Windows Python.

  kb.py roots                      print where each root is on this machine (lib, nc, bridge, page, addons)
  kb.py verify [EXPECTED.json]     compare what is installed with tools/installed.json: one line per difference.
                                   From a repo clone it needs no argument; on a PC without the repo, pass the file
                                   made by `kb.py expected` (run in the repo) instead.
  kb.py expected                   (in the repo) print installed.json with every entry's md5 filled in
  kb.py record                     (in a clone that sees the PC) rewrite the md5s tools/installed.json stores
  kb.py apply DIR [--check]        put a delivery made by kb.deliver.build() in place:
                                     1. the delivery's own files are whole (md5)
                                     2. every file it replaces or adds to still has the md5 the work started from
                                     3. no "new" file is already there with other contents
                                     4. backups to <library>\\_backups\\<task>\\before\\<root>\\...
                                     5. write, then md5-check everything written
                                   --check does 1-3 and writes nothing. Nothing is deleted, ever.
Roots can be moved with tools/pc_roots.json ({"addons": "..."}) or KB_ROOT_ADDONS=... etc."""
import hashlib, io, json, os, sys, tarfile
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))


def roots():
    if os.name == "nt":
        home, app = os.path.expanduser("~"), os.environ.get("APPDATA", "")
        r = {"lib": "D:\\Kitbash Library", "nc": "D:\\new cults",
             "bridge": os.path.join(home, "Desktop", "TIOW Blender bridge"),
             "addons": os.path.join(app, "Blender Foundation", "Blender", "5.1", "scripts", "addons")}
    else:
        m = os.path.expanduser("~/mnt")
        r = {"lib": m + "/d/Kitbash Library", "nc": m + "/d/new cults", "bridge": m + "/Desktop/TIOW Blender bridge",
             "addons": m + "/5.1/scripts/addons"}
    r["page"] = os.path.join(r["bridge"], "Squad Builder")
    f = os.path.join(HERE, "pc_roots.json")
    if os.path.exists(f): r.update(json.load(open(f, encoding="utf-8")))
    for k in list(r):
        if os.environ.get("KB_ROOT_" + k.upper()): r[k] = os.environ["KB_ROOT_" + k.upper()]
    return r


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def at(R, root, rel): return os.path.join(R[root], *rel.replace("\\", "/").split("/"))


def expected():
    out = []
    for e in json.load(open(os.path.join(HERE, "installed.json"), encoding="utf-8"))["files"]:
        e = dict(e)
        if e.get("repo"): e["md5"] = md5(os.path.join(REPO, e["repo"]))
        out.append(e)
    return out


def verify(args):
    exp = json.load(open(args[0], encoding="utf-8")) if args else expected()
    R, bad = roots(), 0
    for e in exp:
        p = at(R, e["root"], e["path"])
        if not os.path.exists(p): bad += 1; print("MISSING  %s: %s" % (e["root"], e["path"])); continue
        if e.get("md5") and not md5(p).startswith(e["md5"]):
            bad += 1; print("DIFFERS  %s: %s  (installed %s, expected %s%s)" % (
                e["root"], e["path"], md5(p)[:8], e["md5"][:8], ", repo " + e["repo"] if e.get("repo") else ""))
    print("%d of %d installed files match" % (len(exp) - bad, len(exp)))
    sys.exit(1 if bad else 0)


def record(_):
    f = os.path.join(HERE, "installed.json"); d = json.load(open(f, encoding="utf-8")); R = roots()
    for e in d["files"]:
        if not e.get("repo"): e["md5"] = md5(at(R, e["root"], e["path"]))[:8]
    open(f, "w", encoding="utf-8", newline="\n").write(json.dumps(d, indent=1) + "\n"); print("recorded")


def payload(D, M):
    data = {}
    for name in M.get("payload", []):
        with tarfile.open(os.path.join(D, name)) as t:
            for m in t.getmembers():
                if m.isfile(): data[m.name] = t.extractfile(m).read()
    return data


def apply(args):
    D = args[0]; check = "--check" in args
    M = json.load(open(os.path.join(D, "manifest.json"), encoding="utf-8")); R = roots()
    bad = [n for n, m in M.get("payload_md5", {}).items() if md5(os.path.join(D, n)) != m]
    if bad: sys.exit("delivery files damaged, commit them again under a new path: %s" % bad)
    data, problems, todo = payload(D, M), [], []
    for e in M["files"]:
        p = at(R, e["root"], e["path"]); mode = e["mode"]
        if mode == "copy":                                  # a file that never leaves the PC (the makers' STLs)
            src = at(R, e["from_root"], e["from"])
            if not os.path.exists(src): problems.append("missing source " + e["from"]); continue
            if md5(src) != e["md5"]: problems.append("source changed " + e["from"]); continue
            blob = None
        else:
            blob = data.get(e["member"])
            if blob is None or hashlib.md5(blob).hexdigest() != e["md5"]: problems.append("payload lacks " + e["path"]); continue
        have = md5(p) if os.path.exists(p) else None
        if mode in ("new", "copy"):
            if have == e["md5"]: continue                   # already there, identical
            if have: problems.append("already there with other contents: %s: %s" % (e["root"], e["path"])); continue
        else:                                               # replace / append
            if have != e.get("base"):
                if have == (e["md5"] if mode == "replace" else e.get("after")): continue      # already done
                problems.append("changed since the work started (%s now, %s then): %s: %s" % (
                    (have or "missing")[:8], (e.get("base") or "missing")[:8], e["root"], e["path"])); continue
        todo.append((e, p, blob))
    if problems: sys.exit("not applied:\n  " + "\n  ".join(problems[:25]) + ("\n  ... %d more" % (len(problems) - 25) if len(problems) > 25 else ""))
    n = {m: sum(1 for e, _, _ in todo if e["mode"] == m) for m in ("new", "copy", "replace", "append")}
    print("ok to apply %s: %d new, %d copied on the PC, %d replaced, %d added to; %d already in place" % (
        M["task"], n["new"], n["copy"], n["replace"], n["append"], len(M["files"]) - len(todo)))
    if check: return
    B = os.path.join(R["lib"], "_backups", M["task"], "before")
    wrote = []
    for e, p, blob in todo:
        if e["mode"] in ("replace", "append") and os.path.exists(p):
            b = at({"x": B}, "x", e["root"] + "/" + e["path"])
            if not os.path.exists(b):
                os.makedirs(os.path.dirname(b), exist_ok=True)
                with open(p, "rb") as s, open(b, "wb") as d: d.write(s.read())
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if e["mode"] == "copy":
            with open(at(R, e["from_root"], e["from"]), "rb") as s, open(p, "wb") as d:
                for chunk in iter(lambda: s.read(1 << 20), b""): d.write(chunk)
            want = e["md5"]
        elif e["mode"] == "append":
            with open(p, "ab") as d: d.write(blob)
            want = e["after"]
        else:
            with open(p, "wb") as d: d.write(blob)
            want = e["md5"]
        wrote.append((e, p, want))
    bad = ["%s: %s" % (e["root"], e["path"]) for e, p, want in wrote if md5(p) != want]
    print("applied %d files; %s; backups in _backups\\%s\\before" % (
        len(wrote), "every md5 matches" if not bad else "MISMATCH: %s" % bad[:10], M["task"]))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "roots": print(json.dumps(roots(), indent=1))
    elif cmd == "expected": print(json.dumps(expected(), indent=1))
    elif cmd in ("verify", "apply", "record"): {"verify": verify, "apply": apply, "record": record}[cmd](sys.argv[2:])
    else: print(__doc__)
