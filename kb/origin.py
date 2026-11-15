"""Origins at the joint (notes 101): a part's file moved into the frame of the socket it hangs from.

A fit says where a part sits on a socket:  part = socket x gap x fit.  Moving the file by its own fit (new point =
fit x old point) puts the joint on the file's origin, and the fit becomes none (identity): the part needs no fit of
its own for that joint. Everything else the sidecar holds in file coordinates is moved with it, so nothing lands
anywhere else than before:

    sockets (and an anchor's three points)   G x socket
    other fits                               fit x inverse(G)
    a maker's copy (variant)                 moved by ITS own fit Gv:  align = Gv x align x inverse(G), and its
                                             sockets and fits as above with Gv

The sidecar keeps "origin": {"from_file": [16], "joint": fit name, "by": ...}: from_file takes the maker's file
coordinates to the file as it is now (it adds up over runs), so a fresh download, Josh's connector blends and the
tools that compare parts in the maker's frame (seat.py, kb.carry, the golden run) still line up; maker_view() gives
a sidecar back in the maker's coordinates.

Sidecar maths is standard library only (tests/kb/t_kb.py runs it); the STL and preview writers need numpy."""
import json, struct

I16 = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
MX16 = [-1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
# what a sidecar may hold for a move to be safe: a key not listed might be in file coordinates, so the part is left
TOP = {"schemaVersion", "part", "category", "sockets", "fits", "notes", "original", "variants", "_about", "exact",
       "ruled", "noPad", "noHand", "mirrorLeft", "adaptor", "origin"}
SOCK = {"type", "name", "matrix", "display_type", "display_size", "props", "points"}
VAR = {"side", "mirror", "align", "name", "folder", "from", "match", "sidecar", "title", "synth", "duplicate"}
VSC = {"sockets", "fits", "category", "notes", "exact", "ruled", "noPad", "noHand", "origin"}


class Skip(Exception):
    """why a part is not moved"""


def mul(a, b):
    return [sum(a[4 * i + k] * b[4 * k + j] for k in range(4)) for i in range(4) for j in range(4)]


def inv(m):
    """inverse of a rigid matrix (rotation transposed)"""
    r = [[m[4 * j + i] for j in range(3)] for i in range(3)]
    t = [-sum(r[i][k] * m[4 * k + 3] for k in range(3)) for i in range(3)]
    return [r[0][0], r[0][1], r[0][2], t[0], r[1][0], r[1][1], r[1][2], t[1], r[2][0], r[2][1], r[2][2], t[2], 0.0, 0.0, 0.0, 1.0]


def point(m, p):
    return [m[4 * i] * p[0] + m[4 * i + 1] * p[1] + m[4 * i + 2] * p[2] + m[4 * i + 3] for i in range(3)]


def _det3(r):
    return (r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1]) - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
            + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]))


def rigid(m):
    """m with its rotation made exactly orthonormal (a fit is stored to 6 places): the mesh must not be skewed"""
    r = [[float(m[4 * i + j]) for j in range(3)] for i in range(3)]
    for _ in range(6):                              # Newton steps to the nearest rotation: R <- (R + inverse(R) transposed) / 2
        d = _det3(r)
        if abs(d) < 1e-9: raise Skip("the fit's rotation is degenerate")
        c = [[(r[(i + 1) % 3][(j + 1) % 3] * r[(i + 2) % 3][(j + 2) % 3] - r[(i + 1) % 3][(j + 2) % 3] * r[(i + 2) % 3][(j + 1) % 3]) / d
              for j in range(3)] for i in range(3)]
        r = [[(r[i][j] + c[i][j]) / 2 for j in range(3)] for i in range(3)]
    if _det3(r) < 0: raise Skip("the fit mirrors the part")
    return [r[0][0], r[0][1], r[0][2], float(m[3]), r[1][0], r[1][1], r[1][2], float(m[7]),
            r[2][0], r[2][1], r[2][2], float(m[11]), 0.0, 0.0, 0.0, 1.0]


def is_identity(m, tol=1e-7):
    return all(abs(a - b) <= tol for a, b in zip(m, I16))


def _r(m): return [round(float(x), 9) + 0.0 for x in m]


def primary(fits, bases, side=None):
    """the fit that is the part's own joint: one of bases (a name, or a name + ' R' / ' L'); with both sides, side's"""
    c = [k for k in fits or {} if k in bases or (k[-2:] in (" R", " L") and k[:-2] in bases)]
    if len(c) > 1 and side: c = [k for k in c if k.endswith(" " + side)] or c
    if len(c) > 1: c = [k for k in c if k.endswith(" R")] or c
    return c[0] if c else None


def side_of(rel):
    return "L" if rel.endswith(" L") or "/Left/" in rel.replace("\\", "/") else "R" if rel.endswith(" R") else None


def from_file(d):
    """the maker's file coordinates -> the file as it is now (16 numbers), or None for a part never moved"""
    o = (d or {}).get("origin")
    m = o.get("from_file") if isinstance(o, dict) else None
    return [float(x) for x in m] if isinstance(m, list) and len(m) == 16 else None


def _moved(d, G, key, by):
    """d (a sidecar, or a variant's) with its sockets and fits moved by G; key's fit becomes none (identity)"""
    Gi = inv(G)
    for s in d.get("sockets") or []:
        if set(s) - SOCK: raise Skip("socket %r has %s" % (s.get("type"), sorted(set(s) - SOCK)))
        s["matrix"] = _r(mul(G, s["matrix"]))
        if isinstance(s.get("points"), list): s["points"] = [_r(point(G, p)) for p in s["points"]]
    for k in list(d.get("fits") or {}):
        d["fits"][k] = list(I16) if k == key else _r(mul(d["fits"][k], Gi))
    was = from_file(d)
    d["origin"] = {"from_file": _r(mul(G, was) if was else G), "joint": key, "by": by}


def move(sc, bases, rel="", by="kb.origin"):
    """(the sidecar after the move, G for the STL, what changed) or Skip. G is None when the file itself stays (its
    joint is on the origin already) though a copy inside the sidecar moved; nothing to do at all raises Skip('done')."""
    if set(sc) - TOP: raise Skip("has %s (not known to be safe to move)" % sorted(set(sc) - TOP))
    try:
        if float(sc.get("scale") or 1.0) != 1.0: raise Skip("has a scale")
    except (TypeError, ValueError): raise Skip("has a scale")
    out = with_joint_fit(json.loads(json.dumps(sc))); did = []
    for v in out.get("variants") or []:
        if isinstance(v, dict) and isinstance(v.get("sidecar"), dict): v["sidecar"] = with_joint_fit(v["sidecar"])
    key = primary(out.get("fits"), bases, side_of(rel))
    G = rigid(out["fits"][key]) if key else list(I16)
    main = not is_identity(G)
    if main: _moved(out, G, key, by); did.append(key)
    for v in out.get("variants") or []:
        if not isinstance(v, dict) or not isinstance(v.get("sidecar"), dict): continue
        if set(v) - VAR or set(v["sidecar"]) - VSC:
            raise Skip("copy %r has %s" % (v.get("name"), sorted((set(v) - VAR) | (set(v["sidecar"]) - VSC))))
        vk = primary(v["sidecar"].get("fits"), bases, v.get("side"))
        Gv = rigid(v["sidecar"]["fits"][vk]) if vk else list(I16)
        if is_identity(Gv) and not main: continue
        A = v.get("align") if isinstance(v.get("align"), list) and len(v["align"]) == 16 else (MX16 if v.get("mirror", True) else I16)
        v["align"] = _r(mul(Gv, mul(A, inv(G))))
        if not is_identity(Gv): _moved(v["sidecar"], Gv, vk, by); did.append("copy %s: %s" % (v.get("name"), vk))
    if not did: raise Skip("done" if key else "no fit for its joint")
    return out, (G if main else None), did


def with_joint_fit(d):
    """d with its joint's fit as identity where the file was moved onto that joint and no fit is stored (notes 101: a
    reader may treat 'origin is the joint' as the fit; TIOW Inbox 1.17.9 and the page index do)"""
    o = (d or {}).get("origin"); jn = o.get("joint") if isinstance(o, dict) else None
    if not jn or jn in (d.get("fits") or {}): return d
    out = json.loads(json.dumps(d)); out.setdefault("fits", {})[jn] = list(I16); return out


def maker_view(sc):
    """the sidecar's own sockets and fits back in the maker's file coordinates (copies inside it are left alone)"""
    G = from_file(sc)
    if not G: return sc
    out = with_joint_fit(json.loads(json.dumps(sc))); Gi = inv(G)
    for s in out.get("sockets") or []:
        s["matrix"] = mul(Gi, s["matrix"])
        if isinstance(s.get("points"), list): s["points"] = [point(Gi, p) for p in s["points"]]
    for k in list(out.get("fits") or {}): out["fits"][k] = mul(out["fits"][k], G)
    return out


# ---------------------------------------------------------------- files (numpy)
STL_DT = [("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]


def move_stl(src, dst, G):
    """a binary STL with every vertex moved by G (header and attribute bytes kept); returns the triangle count"""
    import numpy as np
    raw = open(src, "rb").read(); n = struct.unpack("<I", raw[80:84])[0]
    if 84 + 50 * n != len(raw): raise Skip("not a plain binary STL")
    a = np.frombuffer(raw, dtype=np.dtype(STL_DT), count=n, offset=84).copy()
    M = np.array(G, float).reshape(4, 4); R, t = M[:3, :3], M[:3, 3]
    a["v"] = (a["v"].astype(np.float64) @ R.T + t).astype("<f4")
    a["n"] = (a["n"].astype(np.float64) @ R.T).astype("<f4")
    with open(dst, "wb") as f: f.write(raw[:84]); f.write(a.tobytes())
    return n


def stl_points(path, step=97):
    import numpy as np
    return np.fromfile(path, dtype=np.dtype(STL_DT), offset=84)["v"].reshape(-1, 3)[::step].astype(np.float64)


def move_preview(src, dst, G):
    """a page preview (KBP1) with its vertices moved by G"""
    import numpy as np
    raw = open(src, "rb").read()
    if raw[:4] != b"KBP1": raise Skip("preview isn't KBP1")
    nv = struct.unpack("<I", raw[4:8])[0]
    V = np.frombuffer(raw, dtype="<f4", count=nv * 3, offset=12).reshape(-1, 3).astype(np.float64)
    M = np.array(G, float).reshape(4, 4)
    with open(dst, "wb") as f: f.write(raw[:12]); f.write((V @ M[:3, :3].T + M[:3, 3]).astype("<f4").tobytes()); f.write(raw[12 + nv * 12:])
