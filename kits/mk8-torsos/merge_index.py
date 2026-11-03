"""Add the MK8 delivery's parts (built by minilib.py) to the PC's _builder/index.json in place, with their previews,
and the two new joint types if the index carries joints. No Prepare needed.  python merge_index.py PC_INDEX MINILIB OUT_DIR"""
import json, os, sys, shutil
pc, ml, out = sys.argv[1:4]
raw = open(pc, "rb").read(); d = json.loads(raw)
assert json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode("utf-8") == raw
new = json.load(open(os.path.join(ml, "_builder", "index.json")))
have = {e["path"] for e in d["parts"]}
add = [e for e in new["parts"] if e["path"] not in have]
assert len(add) == len(new["parts"]), "some parts are already in the index"
d["parts"].extend(add)
if isinstance(d.get("joints"), dict):
    for k in ("Chest Equipment", "Neck Guards"): d["joints"][k] = new["joints"][k]
os.makedirs(os.path.join(out, "previews"), exist_ok=True)
for e in add: shutil.copyfile(os.path.join(ml, "_builder", e["prev"]), os.path.join(out, e["prev"]))
open(os.path.join(out, "index.json"), "wb").write(json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
print("added %d parts (%d previews); joints in index: %s; now %d parts" % (len(add), len(add), isinstance(d.get("joints"), dict), len(d["parts"])))
