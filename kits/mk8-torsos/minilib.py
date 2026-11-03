"""Stage the MK8 delivery as a small library (hard links to the built files + _sources.csv rows) and build its
index entries and previews with the page's own build_index.build.  python minilib.py OUT MINILIB"""
import csv, io, json, os, sys
OUT, ML = sys.argv[1:3]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "squad-builder")); import build_index
rows = json.load(open(os.path.join(OUT, "_rows.json")))
SRC = {"Chests": None}
for rel, src, typ, _ in rows:
    p = rel.replace("\\", "/")
    for ext in (".stl", ".sockets.json"):
        a, b = os.path.join(OUT, p[:-4] + ext), os.path.join(ML, p[:-4] + ext)
        os.makedirs(os.path.dirname(b), exist_ok=True)
        if not os.path.exists(b): os.link(a, b)
def src_col(src):        # relative to D:\new cults, as the library's _sources.csv has it
    s = src[len("new cults\\"):] if src.startswith("new cults\\") else src
    return s.split("#")[0]
buf = io.StringIO(newline="")
w = csv.writer(buf, lineterminator="\r\n")
lines = [[rel, src_col(src), typ, ""] for rel, src, typ, _ in rows]
for l in lines: w.writerow(l)
open(os.path.join(ML, "_rows.csv"), "w", newline="", encoding="utf-8").write(buf.getvalue())
open(os.path.join(ML, "_sources.csv"), "w", newline="", encoding="utf-8-sig").write("library path,copied from (D:\\new cults),type,folder fits folded in\r\n" + buf.getvalue())
import shutil; shutil.copyfile(os.path.join(os.path.dirname(__file__), "..", "..", "bridge", "_library.json"), os.path.join(ML, "_library.json"))
build_index.build(ML)
print(len(lines), "rows")
