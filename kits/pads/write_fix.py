"""Write the pad fix: new sidecars (arm Pad sockets, BBoosty/CyberBrush pad fits) under OUT/library/, and the page index
updated in place. Each sidecar keeps its encoding, line ends and indent."""
import sys, os, json, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/pads"); sys.path.insert(0, "/home/claude/kitbash/squad-builder")
from padfix import *
import build_index
OUT = "/mnt/user-data/outputs/pads-2026-11-08"
flat = lambda m: [round(float(x), 6) for x in np.asarray(m).reshape(-1)]
def read(rel):
    b = open(os.path.join(LIB, rel), "rb").read(); bom = b.startswith(b"\xef\xbb\xbf"); raw = b.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in raw else "\n"; second = raw.split(nl)[1] if nl in raw else ""; ind = len(second) - len(second.lstrip(" ")) or None
    return json.loads(raw), (bom, nl, ind)
def write(rel, d, fmt):
    bom, nl, ind = fmt; txt = json.dumps(d, indent=ind, ensure_ascii=False)
    if nl != "\n": txt = txt.replace("\n", nl)
    q = os.path.join(OUT, "library", rel); os.makedirs(os.path.dirname(q), exist_ok=True)
    open(q, "wb").write((b"\xef\xbb\xbf" if bom else b"") + txt.encode("utf-8"))
rel_of = lambda e: e["path"].replace("\\", "/")[:-4] + ".sockets.json"
files = {}
# 1) arm Pad sockets
for r in CHANGE:
    rel = rel_of(r["e"])
    if rel not in files: files[rel] = (r["e"],) + read(rel)
    e, d, fmt = files[rel]; h = d if r["vi"] is None else d["variants"][r["vi"]]["sidecar"]
    t = "Pad " + r["side"]; L = local_socket(r, r["new"])
    for s in h["sockets"]:
        if s["type"] == t:
            old = (s.get("props") or {}).get("tiow_anchor", "")
            s["matrix"] = flat(L)
            s["props"] = {"tiow_anchor": "pose",
                          "tiow_from": "Nov 8 pad fix: Josh's 62 seat from %s, turned about the shoulder joint to this arm's pose (was '%s')" % (r["ref"], old)}
# 2) BBoosty / CyberBrush pad fits: off the old dome sockets, onto the 62 convention
Ki = np.linalg.inv(K); KLi = np.linalg.inv(conj(K)); npad = 0
for e in P:
    if e["maker"] not in DOME: continue
    hs = [e] + list(e.get("variants") or [])
    if not any(t in ("Pad R", "Pad L") for h in hs for t in (h.get("fits") or {})): continue
    rel = rel_of(e); d, fmt = read(rel); files[rel] = (e, d, fmt); npad += 1
    for h in [d] + [v["sidecar"] for v in d.get("variants") or [] if isinstance(v, dict) and isinstance(v.get("sidecar"), dict)]:
        for t, m in list((h.get("fits") or {}).items()):
            if t == "Pad R": h["fits"][t] = flat((Ki @ M(m)))
            elif t == "Pad L": h["fits"][t] = flat((KLi @ M(m)))
            else: continue
            h.setdefault("notes", {})[t + " (Nov 8)"] = "moved with the arms' Pad sockets onto Josh's 62 convention (was set on the old 'dome' sockets; same look on BBoosty/CyberBrush arms)"
for rel, (e, d, fmt) in files.items(): write(rel, d, fmt)
# 3) index in place
idx = json.loads(open("/mnt/user-data/uploads/d/Kitbash Library/_builder/index.json", "rb").read())
byid = {x["id"]: x for x in idx["parts"]}; nidx = 0
for rel, (e, d, fmt) in files.items():
    x = byid[e["id"]]; base = build_index.part_data(d); base.pop("category", None)
    for k in ("fits", "sockets"): x[k] = base[k]
    for ve in x.get("variants") or []:
        v = d["variants"][ve["i"]]["sidecar"]; vb = build_index.part_data(v)
        for k in ("fits", "sockets"): ve[k] = vb[k]
    nidx += 1
os.makedirs(os.path.join(OUT, "_builder"), exist_ok=True)
open(os.path.join(OUT, "_builder", "index.json"), "wb").write(json.dumps(idx, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
json.dump(sorted(files), open(os.path.join(OUT, "changed.json"), "w"), indent=0)
print(len(CHANGE), "arm seats,", npad, "pad files,", len(files), "sidecars written,", nidx, "index entries updated")
