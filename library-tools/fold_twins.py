"""Fold mirror copies into their twin's .sockets.json, then move them out.

    python3 fold_twins.py LIBRARY PAIRS.json HOLDING LOG.csv [--dry] [--budget SECONDS]
                          [--cache MATCHES.json] [--sources LIBRARY/_sources.csv]

PAIRS.json: [{"keep": rel path, "drop": rel path, "same": false}, ...] (paths
relative to LIBRARY, either slash). "same": the drop is the same shape, not
its mirror image (a symmetric pistol shipped as both L and R).

For each pair the drop's mesh is matched onto the keep's (mirrored across X
unless "same"), giving `align`: keep-file coordinates -> drop-file
coordinates. The drop's whole sockets file goes into the keep's sockets file
as a variant:

    "variants": [{"side": "L", "mirror": true, "align": [16 floats],
                  "name": drop file name (no extension), "folder": its folder,
                  "from": its library path, "match": median mm,
                  "sidecar": {its sockets, fits, category, ...}}]

TIOW Inbox 1.16 brings the keep's STL in as that variant (moved by align,
with the variant's sockets and fits) when the part goes on the variant's side,
so the drop is no longer needed. The drop's STL and sockets file are then
moved to HOLDING (same relative path), nothing is deleted. A pair whose
shapes don't match everywhere (median 0.05 mm, 95% within 0.15 mm) is skipped and logged. Resumable: pairs
already in the log are skipped; --cache keeps the shape matches so a dry run's
work is reused. numpy + scipy only.
"""
import csv
import json
import os
import re
import struct
import sys
import time

import numpy as np
from scipy.spatial import cKDTree

SIDECAR = ".sockets.json"
# the copy must match everywhere, not just mostly: Mar Fil re-pose some
# "Mirrored" copies (same triangles, a leg or blade turned), which a mirror
# of the other file can't give back
MATCH_MED = 0.05
MATCH_P95 = 0.15
MX = np.diag([-1.0, 1.0, 1.0])
TOK = re.compile(r"(?i)(?:(?<=[\s_\-\(])|^)(l|r|left|right)(?=$|[\s_\-\)\.])")


def native(rel):
    return rel.replace("\\", os.sep).replace("/", os.sep)


def read_stl(path):
    """Triangle-corner vertices (n*3, 3) of a binary or ASCII STL."""
    with open(path, "rb") as f:
        b = f.read()
    if len(b) >= 84:
        n = struct.unpack("<I", b[80:84])[0]
        if 84 + 50 * n == len(b):
            dt = np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
            return np.frombuffer(b, dtype=dt, count=n, offset=84)["v"].reshape(-1, 3).astype(float)
    txt = b.decode("latin-1")
    nums = re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", txt)
    return np.array(nums, float)


def side_of(rel):
    parts = re.split(r"[\\/]", rel)
    stem = os.path.splitext(parts[-1])[0]
    if re.search(r"(?i)mirror|mirorred", stem) or any(re.search(r"(?i)mirror|mirorred|leftorient", x) for x in parts[:-1]):
        return "L"
    m = re.match(r"(?i)^(L|R)(arm|hand|leg|shoulder|pad)", stem)
    if m:
        return m.group(1).upper()
    m = TOK.search(stem)
    if m:
        return "L" if m.group(1).lower() in ("l", "left") else "R"
    low = [x.lower() for x in parts[:-1]]
    if "left" in low:
        return "L"
    if "right" in low:
        return "R"
    return None


def kabsch(P, Q):
    cp, cq = P.mean(0), Q.mean(0)
    H = (P - cp).T @ (Q - cq)
    U, _S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    return R, cq - R @ cp


def align(K, Dv, mirror):
    """4x4 T with D ~ T @ K (K, Dv: vertex arrays) and the median gap (mm)."""
    B = MX if mirror else np.eye(3)
    rng = np.random.default_rng(0)
    P = K[rng.choice(len(K), min(len(K), 20000), replace=False)] @ B.T
    tgt = Dv[rng.choice(len(Dv), min(len(Dv), 400000), replace=False)] if len(Dv) > 400000 else Dv
    tree = cKDTree(tgt)
    R = np.eye(3)
    t = Dv.mean(0) - (K @ B.T).mean(0)
    d0 = tree.query(P @ R.T + t)[0]
    if np.median(d0) > 0.02:
        for _ in range(60):
            Q = P @ R.T + t
            d, idx = tree.query(Q)
            keep = d <= np.quantile(d, 0.9)
            R2, t2 = kabsch(P[keep], tgt[idx[keep]])
            step = np.linalg.norm(t2 - t) + np.linalg.norm(R2 - R)
            R, t = R2, t2
            if step < 1e-7:
                break
    d = tree.query(P @ R.T + t)[0]
    T = np.eye(4)
    T[:3, :3] = R @ B
    T[:3, 3] = t
    return T, float(np.median(d)), float(np.quantile(d, 0.95))


def match(ks, ds, same):
    """(T, median, p95, mirrored?): the mirror image or the same shape,
    whichever matches (the hinted one first; the other only if it doesn't)."""
    K, Dv = read_stl(ks), read_stl(ds)
    tries = []
    for m in ((False, True) if same else (True, False)):
        tries.append((align(K, Dv, m), m))
        if tries[-1][0][1] <= MATCH_MED and tries[-1][0][2] <= MATCH_P95:
            break
    (T, med, p95), mirror = min(tries, key=lambda x: (x[0][2], x[0][1]))
    return T, med, p95, mirror


def load_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(p, d):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, p)


def folder_fits(stl):
    d = load_json(os.path.join(os.path.dirname(stl), "_fits.json"))
    out = {}
    for t, e in d.items():
        m = e.get("m") if isinstance(e, dict) else e
        if isinstance(m, list) and len(m) == 16:
            out[t] = [float(x) for x in m]
    return out


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    lib, pairs_path, holding, log = a[:4]
    dry = "--dry" in sys.argv
    budget = float(sys.argv[sys.argv.index("--budget") + 1]) if "--budget" in sys.argv else 1e9
    pairs = json.load(open(pairs_path, encoding="utf-8"))
    cache_path = sys.argv[sys.argv.index("--cache") + 1] if "--cache" in sys.argv else None
    cache = load_json(cache_path) if cache_path else None
    done = set()
    if os.path.exists(log):
        with open(log, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                done.add(r["was"])
    new_log = not os.path.exists(log)
    t0 = time.time()
    out = open(log, "a", encoding="utf-8-sig" if new_log else "utf-8", newline="")
    w = csv.writer(out)
    if new_log:
        w.writerow(["was", "now", "kept twin", "kind", "side", "match mm", "p95 mm", "status"])
    n = 0
    for pr in pairs:
        if time.time() - t0 > budget:
            break
        keep, drop, same = pr["keep"], pr["drop"], bool(pr.get("same"))
        if drop in done:
            continue
        ks, ds = os.path.join(lib, native(keep)), os.path.join(lib, native(drop))
        if not (os.path.isfile(ks) and os.path.isfile(ds)):
            w.writerow([drop, "", keep, "", "", "", "", "missing"]); out.flush(); continue
        hit = cache.get(drop) if cache is not None else None
        if hit and hit.get("keep") == keep:
            T, med, p95, mirror = np.array(hit["T"]).reshape(4, 4), hit["med"], hit["p95"], hit["mirror"]
        else:
            try:
                T, med, p95, mirror = match(ks, ds, same)
            except Exception as exc:          # a broken file is logged, not fatal
                w.writerow([drop, "", keep, "", "", "", "", f"error {exc!r}"]); out.flush(); continue
            if cache is not None:
                cache[drop] = {"keep": keep, "T": [float(x) for x in T.ravel()], "med": med, "p95": p95, "mirror": mirror}
                write_json(cache_path, cache)
        same = not mirror
        if med > MATCH_MED or p95 > MATCH_P95:
            w.writerow([drop, "", keep, "same" if same else "mirror", "", f"{med:.3f}", f"{p95:.3f}", "shapes differ, kept both"])
            out.flush(); continue
        kpath = os.path.splitext(ks)[0] + SIDECAR
        dpath = os.path.splitext(ds)[0] + SIDECAR
        kdata, ddata = load_json(kpath), load_json(dpath)
        sub = {k: v for k, v in ddata.items() if k not in ("schemaVersion", "part", "variants", "original")}
        ff = folder_fits(ds)
        if ff:
            fits = dict(ff)
            fits.update(sub.get("fits") or {})
            sub["fits"] = fits
        dside, kside = side_of(drop), side_of(keep)
        rec = {"side": dside, "mirror": not same, "align": [float(x) for x in T.ravel()],
               "name": os.path.splitext(os.path.basename(native(drop)))[0],
               "folder": os.path.basename(os.path.dirname(native(drop))),
               "from": drop, "match": round(med, 4), "sidecar": sub}
        vs = [v for v in (kdata.get("variants") or []) if isinstance(v, dict) and v.get("from") != drop]
        if same and dside == (kside or "R"):
            rec["duplicate"] = True            # the same part twice on the same side
        elif any(v.get("side") == dside and not v.get("duplicate") for v in vs):
            rec["duplicate"] = True
        vs.append(rec)
        kdata.setdefault("schemaVersion", 1)
        kdata.setdefault("part", os.path.splitext(os.path.basename(native(keep)))[0])
        kdata["variants"] = vs
        dest = os.path.join(holding, native(drop))
        status = "dry run" if dry else "moved"
        if not dry:
            write_json(kpath, kdata)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            os.replace(ds, dest)
            if os.path.isfile(dpath):
                os.replace(dpath, os.path.splitext(dest)[0] + SIDECAR)
        shown = os.path.relpath(dest, os.path.dirname(os.path.abspath(lib))).replace(os.sep, "\\")
        w.writerow([drop, shown, keep, "same" if same else "mirror", dside or "", f"{med:.4f}", f"{p95:.4f}",
                    status + (" (duplicate)" if rec.get("duplicate") else "")])
        out.flush()
        n += 1
    out.close()
    left = sum(1 for p in pairs if p["drop"] not in done) - n
    print(f"folded {n}, left {max(left, 0)}")
    if "--sources" in sys.argv and not dry:
        update_sources(sys.argv[sys.argv.index("--sources") + 1], log)


def update_sources(src, log):
    """Take the moved files out of the library index (a copy of it as it was is kept once)."""
    with open(log, encoding="utf-8-sig", newline="") as f:
        moved = {r["was"].replace("/", "\\") for r in csv.DictReader(f) if r["status"].startswith("moved")}
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys()) if rows else []
    keep = [r for r in rows if r.get("library path", "").replace("/", "\\") not in moved]
    if len(keep) == len(rows):
        print("library index: nothing to take out")
        return
    backup = os.path.splitext(src)[0] + ".before-mirrors.csv"
    if not os.path.exists(backup):
        with open(backup, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)
    tmp = src + ".tmp"
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(keep)
    os.replace(tmp, src)
    print(f"library index: {len(rows) - len(keep)} taken out, {len(keep)} left")


if __name__ == "__main__":
    main()
