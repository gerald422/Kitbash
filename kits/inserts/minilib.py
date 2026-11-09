"""Stage the inserts delivery as a small library (links to the built files + _sources.csv rows) and build its index
entries and previews with the page's own build_index.build.  python minilib.py BUILT_LIB MINILIB"""
import csv, io, json, os, shutil, sys
OUT, ML = sys.argv[1:3]
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "squad-builder")); import build_index
m = json.load(open(os.path.join(OUT, "made.json")))
rows = [[m["torso"].replace("/", "\\"), "Desktop\\for inserts.blend", "Chests", ""]] + \
       [[p.replace("/", "\\"), src, "Chest Inserts", ""] for p, src in m["inserts"]]
for rel, _, _, _ in rows:
    p = rel.replace("\\", "/")
    for ext in (".stl", ".sockets.json"):
        a, b = os.path.join(OUT, p[:-4] + ext), os.path.join(ML, p[:-4] + ext)
        os.makedirs(os.path.dirname(b), exist_ok=True)
        if not os.path.exists(b): os.link(a, b)
buf = io.StringIO(newline=""); w = csv.writer(buf, lineterminator="\r\n")
for l in rows: w.writerow(l)
open(os.path.join(ML, "_rows.csv"), "w", newline="", encoding="utf-8").write(buf.getvalue())
open(os.path.join(ML, "_sources.csv"), "w", newline="", encoding="utf-8-sig").write("library path,copied from (D:\\new cults),type,folder fits folded in\r\n" + buf.getvalue())
shutil.copyfile(os.path.join(os.path.dirname(__file__), "..", "..", "bridge", "_library.json"), os.path.join(ML, "_library.json"))
build_index.build(ML)
print(len(rows), "rows")
