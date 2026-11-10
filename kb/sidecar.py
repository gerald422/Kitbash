"""Sidecars (<part>.sockets.json) the way the library keeps them, and the one merge everybody uses.

Format on disk: json indent=1, no final newline, LF or CRLF as the file already is, non-ASCII as the file already is.
save() keeps all of that, so a sidecar that didn't change stays byte-identical (the repo mirrors them byte for byte).
Standard library only (runs on the PC too)."""
import json, math, os

SUFFIX = ".sockets.json"
KEEP_ANCHORS = ("clicked", "copied", "auto")       # props.tiow_anchor values that are Josh's or Prepare's work


def load(path):
    """(data, style). style remembers the file's newline and escaping for save()."""
    raw = open(path, "rb").read()
    text = raw.decode("utf-8-sig")
    d = json.loads(text)
    body = text.replace("\r\n", "\n")
    style = {"crlf": b"\r\n" in raw, "final_newline": body.endswith("\n"),
             "ascii": json.dumps(d, indent=1, ensure_ascii=True) == body.rstrip("\n")
                      and json.dumps(d, indent=1, ensure_ascii=False) != body.rstrip("\n")}
    return d, style


def dumps(d, style=None):
    style = style or {}
    t = json.dumps(d, indent=1, ensure_ascii=bool(style.get("ascii")))
    if style.get("final_newline"): t += "\n"
    if style.get("crlf"): t = t.replace("\n", "\r\n")
    return t.encode("utf-8")


def save(path, d, style=None):
    """Write d. With no style given, an existing file's own style is kept; a new file is LF, UTF-8."""
    if style is None and os.path.exists(path): style = load(path)[1]
    data = dumps(d, style)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f: f.write(data)
    return data


def protected(sock):
    """A socket that must survive a merge: clicked / copied / auto anchors, corrected sockets, held spots."""
    p = sock.get("props") or {}
    return p.get("tiow_anchor") in KEEP_ANCHORS or bool(p.get("tiow_corrected")) or bool(p.get("tiow_holds"))


def _skey(s):
    return (s.get("type"), str((s.get("props") or {}).get("tiow_holds") or ""))


def merge(new, old):
    """new merged into old (what is on the PC now). Returns (merged, kept): kept lists what of old's won.

    - old keys new doesn't mention stay; new's other keys replace old's
    - sockets: a protected old socket beats a new one of the same type (and same tiow_holds); other old sockets are
      replaced by type, and old sockets of types new doesn't have stay
    - fits: new's replace old's, except types in old's "exact" (placed by hand with Fix the Part)
    - "exact" and "ruled" are unions; old's notes stay for the fits that stayed
    - variants are matched by (name, side) and their "sidecar" merged the same way; unmatched ones from both stay"""
    if not old: return json.loads(json.dumps(new)), []
    new, out, kept = json.loads(json.dumps(new)), json.loads(json.dumps(old)), []
    for k, v in new.items():
        if k not in ("sockets", "fits", "notes", "exact", "ruled", "variants"): out[k] = v
    keep = {_skey(s) for s in old.get("sockets") or [] if protected(s)}
    fresh = [s for s in new.get("sockets") or [] if _skey(s) not in keep]
    kept += ["socket " + str(s.get("type")) for s in new.get("sockets") or [] if _skey(s) in keep]
    new_types, socks, placed = {s.get("type") for s in fresh}, [], set()
    for s in old.get("sockets") or []:               # old order is kept; a replaced type takes the old one's place
        t = s.get("type")
        if protected(s) or t not in new_types: socks.append(s)
        elif t not in placed:
            placed.add(t); socks += [n for n in fresh if n.get("type") == t]
    socks += [n for n in fresh if n.get("type") not in placed]
    if socks or "sockets" in old or "sockets" in new: out["sockets"] = socks
    exact = [t for t in old.get("exact") or [] if isinstance(t, str)]
    fits = dict(old.get("fits") or {})
    notes = dict(old.get("notes") or {}) if isinstance(old.get("notes"), dict) else old.get("notes")
    for t, m in (new.get("fits") or {}).items():
        if t in exact and t in fits: kept.append("fit " + t + " (exact)"); continue
        fits[t] = m
        if isinstance(notes, dict) and isinstance(new.get("notes"), dict) and t in new["notes"]: notes[t] = new["notes"][t]
    out["fits"] = fits
    if isinstance(notes, dict) and isinstance(new.get("notes"), dict):
        for t, n in new["notes"].items(): notes.setdefault(t, n)
    if notes is not None: out["notes"] = notes
    elif "notes" in new: out["notes"] = new["notes"]
    ex = exact + [t for t in new.get("exact") or [] if t not in exact]
    if ex: out["exact"] = ex
    if isinstance(old.get("ruled"), dict) or isinstance(new.get("ruled"), dict):
        out["ruled"] = dict(new.get("ruled") or {}, **{k: v for k, v in (old.get("ruled") or {}).items()
                                                      if k in exact or k not in (new.get("fits") or {})})
    if "variants" in new or "variants" in old:
        vk = lambda v: (v.get("name"), v.get("side"))
        olds = {vk(v): v for v in old.get("variants") or []}
        vs, seen = [], set()
        for v in new.get("variants") or []:
            o = olds.get(vk(v)); seen.add(vk(v))
            if o and isinstance(o.get("sidecar"), dict) and isinstance(v.get("sidecar"), dict):
                sc, k2 = merge(v["sidecar"], o["sidecar"]); v = dict(o, **v); v["sidecar"] = sc
                kept += ["variant %s: %s" % (v.get("name"), k) for k in k2]
            vs.append(v)
        out["variants"] = [v for v in old.get("variants") or [] if vk(v) not in seen] + vs
    return out, kept


def _mat_problem(m, rigid=True):
    if not (isinstance(m, list) and len(m) == 16 and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                                       and math.isfinite(x) for x in m)):
        return "not 16 finite numbers"
    if [round(x, 6) for x in m[12:]] != [0, 0, 0, 1]: return "last row isn't 0 0 0 1 (row-major expected)"
    if rigid:
        r = [m[0:3], m[4:7], m[8:11]]
        for i in range(3):
            for j in range(i, 3):
                d = sum(r[k][i] * r[k][j] for k in range(3))
                if abs(d - (1.0 if i == j else 0.0)) > 2e-3: return "rotation part isn't orthonormal (%.4f)" % d
    return None


def problems(d, types=None, rigid=True):
    """What is wrong with a sidecar, as a list of texts (empty = fine). types: the known part types (joints.json)."""
    out = []
    if not isinstance(d, dict): return ["not an object"]
    if d.get("schemaVersion") != 1: out.append("schemaVersion isn't 1")
    c = d.get("category")
    if not isinstance(c, str) or not c: out.append("no category")
    elif types is not None and c not in types: out.append("category %r isn't a known part type" % c)
    if not isinstance(d.get("fits", {}), dict): out.append("fits isn't an object")
    for t, m in (d.get("fits") or {}).items() if isinstance(d.get("fits"), dict) else []:
        p = _mat_problem(m, rigid)
        if p: out.append("fit %r: %s" % (t, p))
    for i, s in enumerate(d.get("sockets") or []):
        if not isinstance(s, dict) or not s.get("type"): out.append("socket %d has no type" % i); continue
        p = _mat_problem(s.get("matrix"), rigid)
        if p: out.append("socket %r: %s" % (s["type"], p))
    for k in ("upright", "offHand"):
        if k in d:
            p = _mat_problem(d[k], rigid)
            if p: out.append("%s: %s" % (k, p))
    for t in d.get("exact") or []:
        if t not in (d.get("fits") or {}): out.append("exact names %r, which has no fit" % t)
    for v in d.get("variants") or []:
        if isinstance(v.get("sidecar"), dict):
            sub = dict(v["sidecar"]); sub.setdefault("schemaVersion", 1); sub.setdefault("category", c or "x")
            out += ["variant %s: %s" % (v.get("name"), p) for p in problems(sub, None, rigid)]
        if "align" in v:
            p = _mat_problem(v["align"], False)
            if p: out.append("variant %s align: %s" % (v.get("name"), p))
    return out
