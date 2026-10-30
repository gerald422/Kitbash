"""Seat Mar Fil's two-armed pieces by their shoulder joints (two_icp.py results): new Shoulder R fit in each
sidecar and in the page's index. Skips pieces already right, poor matches, and anything Josh corrected.
python3 apply_two.py LIB [--go]"""
import json, os, sys, shutil
LIB = sys.argv[1]; GO = "--go" in sys.argv
BK = os.path.join(LIB, "_backups", "two-armed-seat-2026-10-30")
r = json.load(open(os.path.expanduser("~/twoarm/icp_all.json"))); dsc = json.load(open(os.path.expanduser("~/twoarm/two_discs.json")))
idx_p = os.path.join(LIB, "_builder", "index.json"); idx = json.load(open(idx_p, encoding="utf-8")); byid = {p["id"]: p for p in idx["parts"]}
done, held = [], []
for k, v in sorted(r.items(), key=lambda kv: kv[1]["name"]):
    if not (v["move"] > 1.0 or v["rot"] > 5.0): continue
    why = None
    if max(v["medR"], v["medL"]) > 0.3: why = "joint match poor"
    elif k in dsc and max(abs(x) for x in dsc[k]["offR"] + dsc[k]["offL"]) < 0.4: why = "faces already on the sockets"
    rel = v["path"].replace("\\", "/"); sc = os.path.join(LIB, os.path.splitext(rel)[0] + ".sockets.json")
    d = json.load(open(sc, encoding="utf-8"))
    if not why and ("Shoulder R" in (d.get("exact") or []) or (d.get("notes") or {}).get("tiow_corrected")): why = "you corrected it"
    if why: held.append((v["name"], why)); continue
    if GO:
        dst = os.path.join(BK, os.path.splitext(rel)[0] + ".sockets.json"); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(sc, dst)
    fit = [round(x, 6) for x in v["fit"]]
    d.setdefault("fits", {})["Shoulder R"] = fit
    d.setdefault("notes", {})["Shoulder R"] = ("both shoulder joints seated on Shoulder R and L (Mar Fil's joint matched onto the piece, "
                                              "moved %.1f mm, turned %.1f deg; the kit position was off) - Oct 30" % (v["move"], v["rot"]))
    byid[k]["fits"]["Shoulder R"] = fit
    if GO: json.dump(d, open(sc, "w", encoding="utf-8"), indent=1)
    done.append(v["name"])
if GO:
    os.makedirs(BK, exist_ok=True); shutil.copy2(idx_p, os.path.join(BK, "index.json"))
    tmp = idx_p + ".tmp"; json.dump(idx, open(tmp, "w", encoding="utf-8"), separators=(",", ":")); os.replace(tmp, idx_p)
print(len(done), "seated" if GO else "to seat"); [print("  held:", *h) for h in held]
