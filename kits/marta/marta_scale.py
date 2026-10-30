"""Marta's two-armed pieces at 90%: sidecar scale 0.9, fits and sockets in the scaled file's coordinates
(translations x0.9 about the file origin, so the right shoulder stays on Shoulder R), previews and the page's
index updated to match. Backs up every sidecar first. python3 marta_scale.py LIB [--go]
Why 90%: Marta sculpts for 32 mm. Her May 2026 torso matches a Mar Fil chest at 0.90-0.92 (scaled ICP,
scale/torsoscale.py) and her two-armed sets have their shoulder faces 12.2-13.1 mm apart against Mar Fil's
11.1 (0.85-0.91). Run on the device; ran 30 Oct 2026 (32 parts)."""
import json, os, sys, shutil, struct
LIB = sys.argv[1]; GO = "--go" in sys.argv
K = 0.9
TYPES = ("Two-Handed Guns", "Two-Handed Melee", "Heavy Weapons")
BK = os.path.join(LIB, "_backups", "marta-scale-2026-10-30")
idx_p = os.path.join(LIB, "_builder", "index.json")
idx = json.load(open(idx_p, encoding="utf-8"))
def sc16(m, f):
    if isinstance(m, list) and len(m) == 16:
        m = list(m); m[3] *= f; m[7] *= f; m[11] *= f; return m
    if isinstance(m, list) and len(m) == 4 and all(isinstance(r, list) for r in m):
        m = [list(r) for r in m]; m[0][3] *= f; m[1][3] *= f; m[2][3] *= f; return m
    raise ValueError("matrix?")
n = 0
for p in idx["parts"]:
    if p["maker"] != "Marta" or p["type"] not in TYPES:
        continue
    rel = p["path"].replace("\\", "/")
    sc_p = os.path.join(LIB, os.path.splitext(rel)[0] + ".sockets.json")
    d = json.load(open(sc_p, encoding="utf-8"))
    old = float(d.get("scale") or 1.0)
    if abs(old - K) < 1e-9:
        print("already", rel); continue
    f = K / old
    if GO:
        dst = os.path.join(BK, os.path.splitext(rel)[0] + ".sockets.json")
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(sc_p, dst)
    d["fits"] = {t: sc16(m, f) for t, m in (d.get("fits") or {}).items()}
    for s in d.get("sockets") or []:
        s["matrix"] = sc16(s["matrix"], f)
    for v in d.get("variants") or []:
        sd = v.get("sidecar") or {}
        sd["fits"] = {t: sc16(m, f) for t, m in (sd.get("fits") or {}).items()}
        for s in sd.get("sockets") or []:
            s["matrix"] = sc16(s["matrix"], f)
    d["scale"] = K
    d.setdefault("notes", {})["scale"] = "Marta sculpts for 32 mm: at 90% her torso matches Mar Fil's (0.90-0.92) and the shoulders sit 11.0-11.8 mm apart (Josh, 30 Oct)"
    # the page: same change in the index, and the light mesh shrunk to match
    p["fits"] = {t: sc16(m, f) for t, m in p["fits"].items()}
    for s in p.get("sockets") or []:
        s["m"] = sc16(s["m"], f)
    p["scale"] = K
    pv = os.path.join(LIB, "_builder", p["prev"].replace("/", os.sep)) if p.get("prev") else None
    if GO:
        json.dump(d, open(sc_p, "w", encoding="utf-8"), indent=1)
        if pv and os.path.isfile(pv):
            b = bytearray(open(pv, "rb").read()); nv = struct.unpack_from("<I", b, 4)[0]
            vals = struct.unpack_from("<%df" % (nv * 3), b, 12)
            struct.pack_into("<%df" % (nv * 3), b, 12, *[x * f for x in vals])
            open(pv, "wb").write(bytes(b))
    n += 1
    print("%s  x%.3f  %s" % ("done" if GO else "would", f, rel))
if GO:
    shutil.copy2(idx_p, os.path.join(BK, "index.json"))
    tmp = idx_p + ".tmp"; json.dump(idx, open(tmp, "w", encoding="utf-8"), separators=(",", ":")); os.replace(tmp, idx_p)
print(n, "parts", "changed" if GO else "to change")
