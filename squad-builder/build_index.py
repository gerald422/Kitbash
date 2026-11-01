"""Index and preview meshes for the Squad Builder page.

    python3 build_index.py LIBRARY [--budget SECONDS] [--tris 6000] [--no-previews]

Writes LIBRARY/_builder/index.json (every part: name, type, side, sockets,
fits, variants) and LIBRARY/_builder/previews/<id>.bin (a light copy of each
part's mesh for the page to draw: about 6,000 triangles instead of hundreds of
thousands). Run it again after adding parts: unchanged previews are kept, so
it only does the new ones. Resumable with --budget (stops after that many
seconds; run again to carry on). numpy only; fast_simplification is used when
it's installed (better shapes), otherwise a grid simplify.

Preview file: b"KBP1", uint32 vertex count, uint32 triangle count, float32
xyz per vertex (file units, the part's own scale applied), uint32 x3 per
triangle.
"""
import csv
import hashlib
import json
import os
import re
import struct
import sys
import time

import numpy as np

try:
    import fast_simplification
except ImportError:            # the grid simplify below is used instead
    fast_simplification = None

SIDECAR = ".sockets.json"
MAKERS = {"Mar Fil": "MarFil", "Marta PunkGirl": "Marta", "Turtle Ninja": "TN", "BBoosty": "BBoosty",
          "CyberBrush": "CyberBrush", "Springles": "Springles"}


def native(rel):
    return rel.replace("\\", os.sep).replace("/", os.sep)


def read_stl(path):
    """(V float64 (n,3), T int (m,3)) with vertices merged."""
    with open(path, "rb") as f:
        b = f.read()
    tri = None
    if len(b) >= 84:
        n = struct.unpack("<I", b[80:84])[0]
        if 84 + 50 * n == len(b):
            dt = np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
            tri = np.frombuffer(b, dtype=dt, count=n, offset=84)["v"].reshape(-1, 3).astype(np.float64)
    if tri is None:
        nums = re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", b)
        tri = np.array(nums, dtype=np.float64)
    V, inv = np.unique(tri.round(5), axis=0, return_inverse=True)
    return V, inv.reshape(-1, 3)


def simplify(V, T, target):
    if len(T) <= target:
        return V, T
    if fast_simplification is not None:
        try:
            V2, T2 = fast_simplification.simplify(V.astype(np.float32), T.astype(np.int32), 1.0 - target / len(T))
            if len(T2):
                return V2.astype(np.float64), T2
        except Exception:      # fall through to the grid
            pass
    # grid simplify: merge vertices in cells, grow the cell until few enough triangles
    span = (V.max(0) - V.min(0)).max()
    cell = span / 120.0
    for _ in range(12):
        key = np.floor((V - V.min(0)) / cell).astype(np.int64)
        _u, idx, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
        inv = inv.reshape(-1)
        T2 = inv[T]
        T2 = T2[(T2[:, 0] != T2[:, 1]) & (T2[:, 1] != T2[:, 2]) & (T2[:, 0] != T2[:, 2])]
        T2 = np.unique(np.sort(T2, 1), axis=0, return_index=True)[1]
        T2 = inv[T][np.sort(T2)]
        T2 = T2[(T2[:, 0] != T2[:, 1]) & (T2[:, 1] != T2[:, 2]) & (T2[:, 0] != T2[:, 2])]
        if len(T2) <= target * 1.2:
            sums = np.zeros((inv.max() + 1, 3)); cnt = np.zeros(inv.max() + 1)
            np.add.at(sums, inv, V); np.add.at(cnt, inv, 1)
            return sums / cnt[:, None], T2
        cell *= 1.35
    return V, T


def write_preview(path, V, T):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(b"KBP1" + struct.pack("<II", len(V), len(T)))
        f.write(np.asarray(V, "<f4").tobytes())
        f.write(np.asarray(T, "<u4").tobytes())
    os.replace(tmp, path)


def words(*texts):
    w = set()
    for t in texts:
        t = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(t or ""))
        w |= set(re.split(r"[^a-z]+", t.lower()))
    return w


def side_of(name, folder, fits):
    """The inbox's rule: R / L from the maker's name or folder ('-Mirrored' is
    a left), else from the side its sided fits are for."""
    w = words(name, folder)
    r, l = bool(w & {"r", "right", "rh"}), bool(w & {"l", "left", "lh"})
    if r != l:
        return "R" if r else "L"
    if w & {"mirrored", "mirror"}:
        return "L"
    m = re.match(r"^(R|L)(arm|Arm|hand|Hand)", str(name))
    if m:
        return m.group(1)
    ends = {k[-1] for k in fits if re.search(r" [RL]$", k)}
    return ends.pop() if len(ends) == 1 else None


def flat16(m):
    try:
        return [round(float(x), 6) for x in m] if isinstance(m, list) and len(m) == 16 else None
    except (TypeError, ValueError):
        return None


# the fit a part needs for its step in the builder (first word of the fit's name; any side)
SLOT_FITS = {"Legs": ("Waist", "Flat Waist"), "Arms": ("Shoulder",), "Two-Handed Guns": ("Shoulder",),
             "Two-Handed Melee": ("Shoulder",), "Heavy Weapons": ("Shoulder",), "Heads": ("Neck",),
             "Backpacks": ("Back",), "Jump Packs": ("Back",), "Shoulder Pads": ("Pad",), "Knee Pads": ("Shin",),
             "Pistols": ("Hand",), "Melee": ("Hand",), "Shields": ("Hand",), "Hands": ("Hand",),
             "Two-Handed Held": ("Hand",), "Hand-less Weapons": ("Grip",), "Bases": ("Base",)}


def has_slot_fit(e):
    """Has the part (or one of its maker's copies) a fit for its step?"""
    want = SLOT_FITS.get(e.get("type"))
    if not want:
        return True
    names = list(e.get("fits") or {}) + [k for v in e.get("variants") or [] for k in (v.get("fits") or {})]
    return any(n == w or n.startswith(w + " ") for n in names for w in want)


def folder_fits(folder, cache):
    """The fits a folder's _fits.json gives every part in it (Save Fit for Folder)."""
    if folder not in cache:
        out = {}
        try:
            d = json.load(open(os.path.join(folder, "_fits.json"), encoding="utf-8"))
            for k, m in d.items():
                f = flat16(m) if not k.startswith("_") else None
                if f:
                    out[k] = f
        except (OSError, ValueError, AttributeError):
            pass
        cache[folder] = out
    return cache[folder]


def part_data(d):
    """What the page needs from a sockets file (or a variant's)."""
    out = {"fits": {}, "sockets": []}
    for t, m in (d.get("fits") or {}).items():
        f = flat16(m)
        if f:
            out["fits"][t] = f
    for s in d.get("sockets") or []:
        if isinstance(s, dict) and flat16(s.get("matrix")) and s.get("type"):
            e = {"t": str(s["type"]), "m": flat16(s["matrix"])}
            h = (s.get("props") or {}).get("tiow_holds")
            if h:
                e["holds"] = str(h)
            out["sockets"].append(e)
    for k in ("noPad", "noHand"):
        if d.get(k):
            out[k] = True
    if isinstance(d.get("adaptor"), str) and d["adaptor"]:
        out["adaptor"] = d["adaptor"]      # the connector this part brings (a wing's, onto the pack's Wing Mount)
    ex = [str(t) for t in (d.get("exact") or []) if isinstance(t, str)]
    if ex:
        out["exact"] = ex            # fit types corrected by hand in Blender (Save Correction): no settling
    for k in ("upright", "offHand"):
        if flat16(d.get(k)):
            out[k] = flat16(d[k])
    try:
        if float(d.get("scale") or 1.0) != 1.0:
            out["scale"] = float(d["scale"])
    except (TypeError, ValueError):
        pass
    if isinstance(d.get("category"), str):
        out["category"] = d["category"]
    return out


def main():
    lib = sys.argv[1]
    budget = float(sys.argv[sys.argv.index("--budget") + 1]) if "--budget" in sys.argv else 1e9
    target = int(sys.argv[sys.argv.index("--tris") + 1]) if "--tris" in sys.argv else 6000
    build(lib, budget, target, "--no-previews" not in sys.argv)


def default_preview(stl, k, target):
    V, T = read_stl(stl)
    return simplify(V * k, T, target)


def build(lib, budget=1e9, target=6000, previews=True, preview_fn=None):
    """Write the index (and any missing previews). preview_fn(stl, scale, target)
    -> (V, T) makes a preview (Blender's own simplify when run inside Blender)."""
    preview_fn = preview_fn or default_preview
    t0 = time.time()
    outdir = os.path.join(lib, "_builder")
    pdir = os.path.join(outdir, "previews")
    os.makedirs(pdir, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(lib, "_sources.csv"), encoding="utf-8-sig")))
    parts, types, todo = [], {}, 0
    fcache = {}
    ad = os.path.join(outdir, "anchors_done.txt")      # parts prepare_builder.py has worked out anchors for
    anchored = set(open(ad, encoding="utf-8").read().splitlines()) if os.path.isfile(ad) else set()
    for r in rows:
        rel = r["library path"]
        stl = os.path.join(lib, native(rel))
        if not os.path.isfile(stl):
            continue
        try:
            d = json.load(open(os.path.splitext(stl)[0] + SIDECAR, encoding="utf-8"))
        except (OSError, ValueError):
            d = {}
        for tn, spec in (d.get("types") or {}).items():
            if isinstance(spec, dict) and tn not in types:
                e = {"gap": float(spec.get("gap") or 0.0)}
                if spec.get("captured") and flat16(spec.get("mat")):
                    e["mat"] = flat16(spec["mat"])
                types[tn] = e
        parts_ = rel.split("\\")
        stem = os.path.splitext(parts_[-1])[0]
        orig = d.get("original") if isinstance(d.get("original"), dict) else {}
        oname, ofolder = str(orig.get("name") or stem), str(orig.get("folder") or (parts_[-2] if len(parts_) > 1 else ""))
        pid = hashlib.sha1(rel.lower().encode("utf-8")).hexdigest()[:12]
        base = part_data(d)
        for k, f in folder_fits(os.path.dirname(stl), fcache).items():     # the folder's own fits, where the part has none
            base["fits"].setdefault(k, f)
        e = {"id": pid, "path": rel, "name": stem, "orig": oname, "folder": ofolder,
             "type": base.pop("category", None) or r.get("type") or parts_[-2],
             "maker": MAKERS.get(parts_[0].split(" - ")[0], parts_[0]),
             "kit": stem.split(" - ")[0].split(" ", 1)[1] if " - " in stem and " " in stem.split(" - ")[0] else parts_[1] if len(parts_) > 2 else parts_[0],
             "side": side_of(oname, ofolder, base["fits"])}
        e.update(base)
        vs = []
        for i, v in enumerate(d.get("variants") or []):
            if not isinstance(v, dict) or not isinstance(v.get("sidecar"), dict) or v.get("duplicate"):
                continue
            ve = {"i": i, "side": v.get("side"), "mirror": bool(v.get("mirror", True)), "synth": bool(v.get("synth")),
                  "align": flat16(v.get("align")) or [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                  "name": str(v.get("title") or v.get("name") or stem), "orig": str(v.get("name") or "")}
            ve.update(part_data(v["sidecar"]))
            ve.pop("category", None)
            vs.append(ve)
        if vs:
            e["variants"] = vs
        if rel in anchored:
            e["anchored"] = True
        e["prev"] = "previews/" + pid + ".bin"
        pv = os.path.join(pdir, pid + ".bin")
        if previews and (not os.path.isfile(pv) or os.path.getmtime(pv) < os.path.getmtime(stl)):
            if time.time() - t0 < budget:
                try:
                    V2, T2 = preview_fn(stl, float(base.get("scale") or 1.0), target)
                    write_preview(pv, V2, T2)
                except Exception as exc:      # a broken STL gets no preview, not a stopped run
                    print("no preview:", rel, repr(exc))
            else:
                todo += 1
        if os.path.isfile(pv):
            with open(pv, "rb") as f:
                h = f.read(12)
            e["tris"] = struct.unpack("<I", h[8:12])[0] if len(h) == 12 else 0
        else:
            e["prev"] = None
        parts.append(e)
    joints = None
    lj = os.path.join(lib, "_library.json")
    if os.path.isfile(lj):
        try:
            joints = json.load(open(lj, encoding="utf-8")).get("joints")
        except (OSError, ValueError):
            joints = None
    idx = {"version": 1, "built": time.strftime("%Y-%m-%d %H:%M"), "parts": parts, "types": types}
    if joints:
        idx["joints"] = joints
    tmp = os.path.join(outdir, "index.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx, f, separators=(",", ":"))
    os.replace(tmp, os.path.join(outdir, "index.json"))
    have = sum(1 for p in parts if p["prev"])
    print(f"{len(parts)} parts indexed, {have} with previews" + (f", {todo} previews still to make (run again)" if todo else ""))
    # parts with no fit yet: Blender parks them beside the model to be placed by eye (then Save Fit for Folder)
    nofit = sorted((p["type"], p["path"]) for p in parts if not has_slot_fit(p))
    with open(os.path.join(outdir, "no_fit.txt"), "w", encoding="utf-8") as f:
        f.write("Parts with no fit yet for their step: Blender parks them beside the model to be placed by eye.\n"
                "Place one and use Save Fit for Folder, and the rest of its folder follows.\n\n")
        for t, rel in nofit:
            f.write(f"{t}\t{rel}\n")
    if nofit:
        print(f"{len(nofit)} parts have no fit yet: listed in _builder\\no_fit.txt")
    return todo


if __name__ == "__main__":
    main()
