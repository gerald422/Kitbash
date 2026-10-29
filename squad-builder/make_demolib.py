"""A demo Kitbash Library in the real layout, from the kit files in this container.

Rows of Josh's library index (before the mirror copies went) whose source STL
is here get the STL (symlinked) and the test library's sockets file at their
library path; then the real mirror-copy pairs are folded (fold_twins.py) and
the real rename plan applied (rename_library.py) - so the result is laid out
and named exactly as D:\\Kitbash Library is now."""
import csv, json, os, shutil, subprocess, sys

UP = "/mnt/user-data/uploads/d/Kitbash Library"
NC = "/mnt/user-data/uploads/new cults"
KIT = "/home/claude/test/kitlib"
NCL = "/home/claude/test/nclib"
OUT = "/home/claude/builder/demolib"
FOLD = "/home/claude/fold"


def src_of(copied):
    rel = copied.replace("\\", "/")
    for base in (NC, "/home/claude/raw"):
        p = os.path.join(base, rel)
        if os.path.isfile(p):
            return p
    if rel.startswith("All Mar All the time/AssaultMarines-V2/"):
        p = "/home/claude/raw/" + rel[len("All Mar All the time/"):]
        if os.path.isfile(p):
            return p
    return None


def sidecar_of(copied):
    rel = os.path.splitext(copied.replace("\\", "/"))[0] + ".sockets.json"
    for base in (KIT, NCL):
        p = os.path.join(base, rel)
        if os.path.isfile(p):
            return p
    if rel.startswith("All Mar All the time/AssaultMarines-V2/"):
        p = os.path.join(KIT, rel)
        if os.path.isfile(p):
            return p
    return None


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    rows = list(csv.DictReader(open(UP + "/_sources.before-mirrors.csv", encoding="utf-8-sig")))
    fields = list(rows[0].keys())
    kept, nos = [], 0
    for r in rows:
        s = src_of(r["copied from (D:\\new cults)"])
        if not s:
            continue
        dst = os.path.join(OUT, r["library path"].replace("\\", "/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.symlink(s, dst)
        sc = sidecar_of(r["copied from (D:\\new cults)"])
        d = json.load(open(sc)) if sc else {"schemaVersion": 1, "sockets": [], "fits": {}}
        d["category"] = r["type"]
        nos += not sc
        json.dump(d, open(os.path.splitext(dst)[0] + ".sockets.json", "w"), indent=1)
        kept.append(r)
    with open(OUT + "/_sources.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(kept)
    print(f"{len(kept)} parts ({nos} without a sockets file in the test library)")
    # the real mirror-copy pairs that are both here
    have = {r["library path"] for r in kept}
    pairs = [{"keep": m["kept twin"], "drop": m["was"], "same": m["kind"] == "same"}
             for m in csv.DictReader(open(UP + "/_mirror_copies.csv", encoding="utf-8-sig"))
             if m["kept twin"] in have and m["was"] in have]
    json.dump(pairs, open("/home/claude/builder/demo_pairs.json", "w"))
    print(len(pairs), "mirror pairs to fold")
    subprocess.run([sys.executable, FOLD + "/fold_twins.py", OUT, "/home/claude/builder/demo_pairs.json",
                    "/home/claude/builder/demo_holding", OUT + "/_mirror_copies.csv",
                    "--sources", OUT + "/_sources.csv", "--cache", "/home/claude/builder/demo_fold_cache.json"], check=True)
    subprocess.run([sys.executable, FOLD + "/rename_library.py", OUT, FOLD + "/names_all.csv", OUT + "/_renamed.csv"], check=True)


if __name__ == "__main__":
    main()
