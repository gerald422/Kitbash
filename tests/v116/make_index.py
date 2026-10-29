"""A library index (_sources.csv) for a test library: every STL, type from its folder."""
import csv, os, sys
lib = sys.argv[1]
rows = []
for d, _s, fs in os.walk(lib):
    for f in fs:
        if f.lower().endswith(".stl"):
            rel = os.path.relpath(os.path.join(d, f), lib).replace(os.sep, "\\")
            rows.append({"library path": rel, "copied from (D:\\new cults)": rel, "type": os.path.basename(d), "folder fits folded in": ""})
rows.sort(key=lambda r: r["library path"])
with open(os.path.join(lib, "_sources.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "rows")
