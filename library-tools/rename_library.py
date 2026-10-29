"""Rename library parts to the names in a plan (plan_names.py), or put them back.

    python3 rename_library.py LIBRARY names.csv LOG.csv [--dry] [--budget SECONDS]
    python3 rename_library.py LIBRARY --undo LOG.csv

Each STL and its .sockets.json get the new name in the same folder. The
sockets file keeps the maker's name ("original": name, folder, path), which
TIOW Inbox 1.16 reads for its side and pairing rules, and a variant folded in
from a mirror copy gets its own readable "title". _sources.csv follows (a
copy of it as it was is kept once). Resumable: files already in the log are
skipped. Nothing is deleted.
"""
import csv
import json
import os
import sys
import time

SIDECAR = ".sockets.json"


def native(rel):
    return rel.replace("\\", os.sep).replace("/", os.sep)


def load_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def write_json(p, d):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, p)


def read_log(log):
    if not os.path.exists(log):
        return []
    with open(log, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def update_sources(lib, mapping):
    src = os.path.join(lib, "_sources.csv")
    if not os.path.exists(src):
        return
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys()) if rows else []
    backup = os.path.join(lib, "_sources.before-rename.csv")
    if not os.path.exists(backup):
        with open(backup, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)
    n = 0
    for r in rows:
        p = r.get("library path", "")
        if p in mapping:
            r["library path"] = mapping[p]
            n += 1
    tmp = src + ".tmp"
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)
    os.replace(tmp, src)
    print(f"library index: {n} paths updated")


def undo(lib, log):
    rows = [r for r in read_log(log) if r["status"] == "renamed"]
    back = {}
    for r in reversed(rows):
        a, b = os.path.join(lib, native(r["now"])), os.path.join(lib, native(r["was"]))
        if os.path.isfile(a) and not os.path.exists(b):
            os.replace(a, b)
            sa, sb = os.path.splitext(a)[0] + SIDECAR, os.path.splitext(b)[0] + SIDECAR
            if os.path.isfile(sa) and not os.path.exists(sb):
                os.replace(sa, sb)
            back[r["now"]] = r["was"]
    update_sources(lib, back)
    os.replace(log, log + ".undone")
    print(f"put back {len(back)}")


def main():
    lib = sys.argv[1]
    if "--undo" in sys.argv:
        undo(lib, sys.argv[sys.argv.index("--undo") + 1])
        return
    a = [x for x in sys.argv[2:] if not x.startswith("--")]
    plan_path, log = a[0], a[1]
    dry = "--dry" in sys.argv
    budget = float(sys.argv[sys.argv.index("--budget") + 1]) if "--budget" in sys.argv else 1e9
    with open(plan_path, encoding="utf-8-sig", newline="") as f:
        plan = list(csv.DictReader(f))
    title = {}                                # every planned name, for variants' titles
    for r in plan:
        title[r["library path"].replace("/", "\\")] = r["new name"]
    done = {r["was"] for r in read_log(log)}
    new_log = not os.path.exists(log)
    out = open(log, "a", encoding="utf-8-sig" if new_log else "utf-8", newline="")
    w = csv.writer(out)
    if new_log:
        w.writerow(["was", "now", "status"])
    t0 = time.time()
    n = 0
    mapping = {}
    for r in plan:
        if time.time() - t0 > budget:
            break
        old, new = r["library path"], r["new path"]
        if old in done or old == new:
            continue
        a_, b_ = os.path.join(lib, native(old)), os.path.join(lib, native(new))
        if not os.path.isfile(a_):
            continue                           # not in the library (a mirror copy that was folded in)
        if os.path.exists(b_) and os.path.normcase(a_) != os.path.normcase(b_):
            w.writerow([old, new, "name taken, kept"]); out.flush(); continue
        sa, sb = os.path.splitext(a_)[0] + SIDECAR, os.path.splitext(b_)[0] + SIDECAR
        data = load_json(sa)
        if data is None:                       # no sockets file yet: one just for the maker's name
            data = {"schemaVersion": 1, "part": os.path.splitext(os.path.basename(native(old)))[0], "sockets": []}
        if dry:
            w.writerow([old, new, "dry run"]); out.flush(); n += 1; continue
        if not isinstance(data.get("original"), dict):
            parts = old.replace("/", "\\").split("\\")
            data["original"] = {"name": os.path.splitext(parts[-1])[0],
                                "folder": parts[-2] if len(parts) > 1 else "", "path": old}
        for v in data.get("variants") or []:
            if isinstance(v, dict) and v.get("from"):
                t = title.get(str(v["from"]).replace("/", "\\"))
                if t:
                    v["title"] = t
        write_json(sa, data)
        if os.path.normcase(sa) != os.path.normcase(sb):
            os.replace(sa, sb)
        os.replace(a_, b_)
        w.writerow([old, new, "renamed"]); out.flush()
        mapping[old] = new
        n += 1
    out.close()
    if not dry:
        allmap = {r["was"]: r["now"] for r in read_log(log) if r["status"] == "renamed"}
        update_sources(lib, allmap)
    print(f"renamed {n}")


if __name__ == "__main__":
    main()
