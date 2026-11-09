"""Stage the WarGame Exclusive parts as a small library (the maker's files under their library names + sidecars +
_sources.csv rows) and build their index entries and previews with the page's own build_index.build.
python minilib.py SC_DIR MINILIB"""
import csv, io, json, os, shutil, sys
SC, ML = sys.argv[1:3]
U = "/mnt/user-data/uploads/d/new cults/"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "squad-builder")); import build_index
rows = []
for rel, cat, _fit, lib in json.load(open(os.path.join(SC, "list.json"))):
    dst = os.path.join(ML, *lib.split("\\")); os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst): os.link(U + rel, dst)
    shutil.copyfile(os.path.join(SC, rel[:-4] + ".sockets.json"), dst[:-4] + ".sockets.json")
    rows.append([lib, rel.replace("/", "\\"), cat, ""])
buf = io.StringIO(newline=""); w = csv.writer(buf, lineterminator="\r\n")
for r in rows: w.writerow(r)
open(os.path.join(ML, "_rows.csv"), "w", newline="", encoding="utf-8").write(buf.getvalue())
open(os.path.join(ML, "_sources.csv"), "w", newline="", encoding="utf-8-sig").write("library path,copied from (D:\\new cults),type,folder fits folded in\r\n" + buf.getvalue())
shutil.copyfile(os.path.join(os.path.dirname(__file__), "..", "..", "bridge", "_library.json"), os.path.join(ML, "_library.json"))
build_index.build(ML)
print(len(rows), "rows")
