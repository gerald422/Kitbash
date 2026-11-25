"""Scale a maker's parts (Josh, Nov 25: BBoosty is heresy scale, "would need to go up by 10%"; as Springles, notes 029, 114).

    python tools/rescale_maker.py "BBoosty - Heresy" 1.1 [--check]

Every sidecar under the maker's folder (library and the repo's mirror) gets `scale` x K (TIOW and the batch builder
scale the mesh by it on import), and every position in the part's own coordinates x K: sockets, fits, offHand, pivot,
variant aligns, and the same inside each variant's sidecar (TIOW reads a variant's scale from the variant). So every
joint keeps its place on the mesh and the part grows about it. A notes.Scale line says so. Backs up first to
`_backups/<maker> scale <date>/before`."""
import os, sys, glob, json, shutil, time
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)
from kb import sidecar as SC

LIB = "D:/Kitbash Library"


def m16(m, k):
    return [round(float(x) * k, 6) if i in (3, 7, 11) else x for i, x in enumerate(m)]


def scale_side(d, k, top):
    n = 0
    for s in d.get("sockets") or []:
        if isinstance(s.get("matrix"), list) and len(s["matrix"]) == 16: s["matrix"] = m16(s["matrix"], k); n += 1
    for t, f in list((d.get("fits") or {}).items()):
        if isinstance(f, list) and len(f) == 16: d["fits"][t] = m16(f, k); n += 1
    if isinstance(d.get("offHand"), list) and len(d["offHand"]) == 16: d["offHand"] = m16(d["offHand"], k); n += 1
    if isinstance(d.get("pivot"), list) and len(d["pivot"]) == 3: d["pivot"] = [round(float(x) * k, 6) for x in d["pivot"]]; n += 1
    old = float(d.get("scale") or 1.0); d["scale"] = round(old * k, 6)
    if top:
        d.setdefault("notes", {})
        if isinstance(d["notes"], dict):
            d["notes"]["Scale"] = ("x%g on %s (heresy scale, Josh): mesh scaled on import; every socket's, fit's, offHand's and "
                                   "pivot's move scaled with it, so each joint keeps its place on the mesh" % (k, time.strftime("%Y-%m-%d")))
        for v in d.get("variants") or []:
            if isinstance(v.get("align"), list) and len(v["align"]) == 16: v["align"] = m16(v["align"], k)
            if isinstance(v.get("sidecar"), dict): n += scale_side(v["sidecar"], k, False)
    return n


def main(A):
    maker, k = A[0], float(A[1]); check = "--check" in A
    files = sorted(glob.glob(os.path.join(LIB, maker, "**", "*" + SC.SUFFIX), recursive=True))
    already = [f for f in files if json.load(open(f, encoding="utf-8-sig")).get("scale")]
    if already: raise SystemExit("already scaled, nothing done: %d files, e.g. %s" % (len(already), already[0]))
    bk = os.path.join(LIB, "_backups", "%s scale %s" % (maker, time.strftime("%Y-%m-%d %H%M")), "before")
    tot = 0
    for f in files:
        rel = os.path.relpath(f, LIB)
        d, style = SC.load(f); tot += scale_side(d, k, True)
        if check: continue
        os.makedirs(os.path.dirname(os.path.join(bk, rel)), exist_ok=True); shutil.copy2(f, os.path.join(bk, rel))
        SC.save(f, d, style)
        mirror = os.path.join(REPO, "library", rel)
        if os.path.exists(mirror): SC.save(mirror, d, style)
    print("%d sidecars, %d positions x%g%s" % (len(files), tot, k, " (--check: nothing written)" if check else "; backup " + bk))


if __name__ == "__main__":
    main(sys.argv[1:])
