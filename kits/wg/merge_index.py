"""Add the inserts delivery's parts (built by minilib.py) to the PC's _builder/index.json in place, with their previews,
and the new joint type if the index carries joints. No Prepare needed.  python merge_index.py PC_INDEX MINILIB OUT_DIR"""
import json, os, sys, shutil
pc, ml, out = sys.argv[1:4]
raw = open(pc, "rb").read(); d = json.loads(raw)
# Prepare writes it compact and ASCII-escaped (since Nov 6); older in-place merges wrote UTF-8: keep whichever it is
ASCII = next(a for a in (True, False) if json.dumps(d, separators=(",", ":"), ensure_ascii=a).encode("utf-8") == raw)
new = json.load(open(os.path.join(ml, "_builder", "index.json")))
have = {e["path"] for e in d["parts"]}
add = [e for e in new["parts"] if e["path"] not in have]
assert len(add) == len(new["parts"]), "some parts are already in the index"
d["parts"].extend(add)
if isinstance(d.get("joints"), dict):
    for k in (): d["joints"][k] = new["joints"][k]
os.makedirs(os.path.join(out, "previews"), exist_ok=True)
for e in add: shutil.copyfile(os.path.join(ml, "_builder", e["prev"]), os.path.join(out, e["prev"]))
open(os.path.join(out, "index.json"), "wb").write(json.dumps(d, separators=(",", ":"), ensure_ascii=ASCII).encode("utf-8"))
print("added %d parts (%d previews); joints in index: %s; now %d parts" % (len(add), len(add), isinstance(d.get("joints"), dict), len(d["parts"])))
