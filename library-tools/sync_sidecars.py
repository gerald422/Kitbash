"""Copy the library's sidecars (and its index CSVs) between the Kitbash Library
and this repository's library/ folder. STLs are never copied.

    python sync_sidecars.py export "D:\\Kitbash Library" library    library -> repo (before a commit)
    python sync_sidecars.py import library "D:\\Kitbash Library"    repo -> library (to roll back)

Only files that differ are written. --prune also removes sidecars from the
destination that are gone from the source (off by default)."""
import filecmp
import os
import shutil
import sys

KEEP_NAMES = {"_fits.json", "_sources.csv", "_renamed.csv", "_bases_moved.csv", "_mirror_copies.csv"}
SKIP_DIRS = {"_builder", ".git", "__pycache__"}


def wanted(name):
    return name.endswith(".sockets.json") or name in KEEP_NAMES


def files(root):
    out = {}
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for n in names:
            if wanted(n):
                p = os.path.join(d, n)
                out[os.path.relpath(p, root)] = p
    return out


def sync(src, dst, prune=False):
    have, there = files(src), files(dst)
    new = changed = gone = 0
    for rel, p in sorted(have.items()):
        q = os.path.join(dst, rel)
        if rel in there and filecmp.cmp(p, q, shallow=False):
            continue
        os.makedirs(os.path.dirname(q), exist_ok=True)
        shutil.copy2(p, q)
        if rel in there:
            changed += 1
        else:
            new += 1
    for rel in sorted(set(there) - set(have)):
        if prune:
            os.remove(there[rel])
        gone += 1
    print(f"{new} new, {changed} changed, {gone} {'removed' if prune else 'only in the destination (use --prune to remove)'}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 3 or args[0] not in ("export", "import"):
        sys.exit(__doc__)
    sync(args[1], args[2], prune="--prune" in sys.argv)
