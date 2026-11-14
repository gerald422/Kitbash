"""Item 3: fits for the library parts that have none, carried from the fitted parts of the same maker (kb.carry).

    PY  carry_library.py ext   LIBRARY WORK                      box sizes of every fitted / unfitted part (numpy only)
    PY  carry_library.py shapes LIBRARY WORK [--shard I/N]        the fitted parts' surface samples -> WORK/shapes (0.7 MB
                                                                  each), so the shards don't all read the library's drive
    BL  carry_library.py run   LIBRARY WORK [--types A,B] [--shard I/N]      the unfitted parts -> WORK/run-I.jsonl
    BL  carry_library.py again LIBRARY WORK [--shard I/N]        torsos that got some joints but not all from their folder
                                                                  (a posed torso beside one-pose ones): the missing
                                                                  joints once more, matched with turning -> WORK/run-zz-*.jsonl
    BL  carry_library.py loo   LIBRARY WORK [--types A,B] [--shard I/N] [--per 12] [--scope folder|maker] [--mode rigid]
                                                                  leave-one-out on fitted parts -> WORK/loo-<scope>-I.jsonl
    PY  carry_library.py report WORK [loo-folder|loo-maker|run]   what was kept / right / dropped, by type and maker
    PY  carry_library.py test  LIBRARY WORK [--per 4]             a subset built with TIOW Inbox (tests/creator/t_creator.py):
                                                                  the loosest and the middle kept parts of each type
    PY  carry_library.py build LIBRARY WORK TASK                  merge what was kept into the sidecars -> WORK/deliver
                                                                  (tools/kb.py apply WORK/deliver [--check])
  PY = a Python with numpy (Blender's own); BL = blender --background --factory-startup --python ... --  (the KD tree).
  run and loo keep what they have done (a stopped run carries on); shards split the parts so several can run at once.

Where a part's references come from: the fitted parts of its type in its own library folder; when that keeps nothing
(or there are none), the fitted parts of its type anywhere under the same maker (top folder), which kb.carry then
treats by how they relate (mostly `rigid`, its strictest gates). Heads whose maker has no fitted head, or that no
reference matches, go through the head rule (kb.fit.Heads: Josh's Assault helmet 1, neck ring within 0.30 mm).
Torsos also take the reference's `upright`. Nothing is written to the library here: build makes a delivery.

A torso is used only when it got both shoulders, the neck and a waist: with fewer nothing can be built on it.
run tries all of that; what is USED (report, test, build) is POLICY, set from the leave-one-out of Nov 14 (notes 093):
only the sources that kept nothing wrong. Folder-mates: torsos 192 of 192 joints right, legs 25 of 25, arms 62 of 65,
pads 9 of 9 in `same` / `turn` (43 of 53 in `rigid`: not used). Same maker elsewhere: torsos 24 of 24; heads 4 of 9
and pads 7 of 12 right, arms 4 of 5: not used. The head rule put Marta's helmets on at any heading (their necks are
balls, not rings): not used.
"""
import sys, os, json, time, glob, random, collections, hashlib
import numpy as np
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, REPO)
TYPES = ["Arms", "Legs", "Chests", "Heads", "Shoulder Pads"]
HEAD_MAX = 0.30                                          # add_creator's gate for the head rule
SAME_REGION = 0.12                                       # a copied (kit frame) joint: its region has to lie on the part
ALL = ("same", "turn", "rigid")
POLICY = {"Arms": {"folder": ALL}, "Legs": {"folder": ALL}, "Chests": {"folder": ALL, "maker": ALL},
          "Shoulder Pads": {"folder": ("same", "turn")}, "Heads": {}}


def used(g):
    """the result with only what POLICY allows left in it (None when nothing is)"""
    ok = POLICY.get(g["cat"], {}).get(g["scope"], ())
    names = {n for n, h in g["how"].items() if h["mode"] in ok}
    fits = {n: F for n, F in g["fits"].items() if n in names}
    if g["cat"] == "Chests":
        socks = [s for s in g["sockets"] if s["type"] in names or (s["type"] not in g["how"] and names)]; t = {s["type"] for s in socks}
        if not ({"Shoulder R", "Shoulder L", "Neck"} <= t and t & {"Waist", "Flat Waist"}): return None    # a torso needs all of them to be built on
    else: socks = g["sockets"] if fits else []
    if not fits and not socks: return None
    return dict(g, fits=fits, sockets=socks)


def scan(lib, types):
    """{cat: [(rel without suffix, sidecar)]} for every part of these types"""
    from kb import carry
    out = collections.defaultdict(list)
    for d, dn, fs in os.walk(lib):
        dn[:] = sorted(x for x in dn if not x.startswith("_"))
        for f in sorted(fs):
            if not f.endswith(".sockets.json"): continue
            try: sc = json.load(open(os.path.join(d, f), encoding="utf-8-sig"))
            except ValueError: continue
            if sc.get("category") in types and os.path.exists(os.path.join(d, f[:-13] + ".stl")):
                out[sc["category"]].append((os.path.relpath(os.path.join(d, f[:-13]), lib).replace("\\", "/"), sc))
    return out
def fitted(cat, sc):
    from kb import carry
    return bool(carry.joints(cat, sc))
def maker(rel): return rel.split("/")[0]
def folder(rel): return os.path.dirname(rel)
def opt(A, name, default=None):
    return A[A.index(name) + 1] if name in A else default


def ext(lib, work, types):
    from kb import carry
    f = work + "/ext.json"; E = json.load(open(f)) if os.path.exists(f) else {}
    P = scan(lib, types); todo = [(rel, sc) for c in P for rel, sc in P[c] if rel not in E]; t0 = time.time()
    for i, (rel, sc) in enumerate(todo):
        try: E[rel] = [round(float(x), 3) for x in np.sort(np.ptp(carry.soup(lib + "/" + rel + ".stl", sc.get("scale", 1.0)).reshape(-1, 3), 0))]
        except (OSError, ValueError) as e: E[rel] = None; print("unreadable:", rel, e)
        if i % 200 == 199: json.dump(E, open(f, "w")); print("  %d of %d (%.0f s)" % (i + 1, len(todo), time.time() - t0), flush=True)
    json.dump(E, open(f, "w")); print("ext: %d parts, %d new" % (len(E), len(todo)))


def cache_file(work, rel): return "%s/shapes/%s.npy" % (work, hashlib.md5(rel.encode("utf-8")).hexdigest())
def make_ref(work, rel, sc, path):
    """a kb.carry.Ref whose shape comes from WORK/shapes when it is there (the same 60,000 points Shape would draw)"""
    from kb import carry
    class CRef(carry.Ref):
        @property
        def shape(self):
            if self._shape is None:
                f = cache_file(self.work, self.rel)
                if not os.path.exists(f): self._shape = carry.Shape(self.path, self.sc.get("scale", 1.0), 1, self.mirror)
                else:
                    sh = carry.Shape.__new__(carry.Shape); sh.S = np.load(f).astype(float) * (np.array([-1.0, 1, 1]) if self.mirror else 1.0)
                    sh.full = sh.S[np.random.default_rng(2).choice(60000, 3000, replace=False)]; sh.V, sh.ext, sh._tree, sh.whole = None, self.ext, None, {}
                    self._shape = sh
            return self._shape
        def mirrored(self):
            r = carry.Ref.mirrored(self); r.rel, r.work, r._ext = self.rel, self.work, self._ext; return r
    r = CRef(os.path.basename(rel), sc, path); r.rel, r.work = rel, work; return r


def shapes(lib, work, A):
    from kb import carry
    i, n = shard_of(A); os.makedirs(work + "/shapes", exist_ok=True); P = scan(lib, TYPES); t0 = time.time()
    todo = [(rel, sc) for c in sorted(P) for rel, sc in P[c] if fitted(c, sc)][i::n]; k = 0
    for rel, sc in todo:
        f = cache_file(work, rel)
        if os.path.exists(f): continue
        try: np.save(f, carry.Shape(lib + "/" + rel + ".stl", sc.get("scale", 1.0), 1).S.astype(np.float32)); k += 1
        except (OSError, ValueError) as e: print("unreadable:", rel, e)
        if k % 100 == 99: print("  %d (%.0f s)" % (k + 1, time.time() - t0), flush=True)
    print("shapes shard %d: %d of %d new (%.0f s)" % (i, k, len(todo), time.time() - t0))


class Lib:
    """the library's parts of the chosen types, their references (one Ref a part, its shape read when needed)"""
    def __init__(self, lib, work, types):
        from kb import carry
        self.lib, self.work, self.P = lib, work, scan(lib, types); self.refs = {}; self.live = []
        E = json.load(open(work + "/ext.json")) if os.path.exists(work + "/ext.json") else {}
        for cat in self.P:
            for rel, sc in self.P[cat]:
                if not fitted(cat, sc): continue
                r = make_ref(work, rel, sc, lib + "/" + rel + ".stl")
                if E.get(rel): r._ext = np.array(E[rel])
                self.refs[rel] = r
    def mates(self, cat, rel, scope, hide=()):
        if scope == "folder": return [r for q, r in self.refs.items() if folder(q) == folder(rel) and r.sc["category"] == cat and q not in hide]
        return [r for q, r in self.refs.items() if maker(q) == maker(rel) and folder(q) != folder(rel) and r.sc["category"] == cat and q not in hide]
    def tidy(self, used, cap=70):
        """keep at most `cap` reference shapes in memory (a maker has hundreds)"""
        for r in used:
            if r in self.live: self.live.remove(r)
            self.live.append(r)
        while len(self.live) > cap: self.live.pop(0)._shape = None


def set_upright(L, rel, g, hide=()):
    """a torso's standing-up turn: its reference's, moved with the waist joint (so the legs under a posed torso stand
    straight and the chest keeps its pose); with no waist carried, with the best-matched joint"""
    from kb import carry
    have = [s["type"] for s in g["sockets"] if s["type"] in g["how"]]
    if not have: return
    n = next((t for t in ("Waist", "Flat Waist") if t in have), None) or min(have, key=lambda n: g["how"][n]["match"])
    r = next((r for r in L.mates("Chests", rel, g["scope"], hide) if r.name == g["how"][n]["from"]), None)
    if r is not None and r.sc.get("upright"):
        S0 = next(np.array(s["matrix"]).reshape(4, 4) for s in r.sc["sockets"] if s["type"] == n)
        S1 = next(np.array(s["matrix"]).reshape(4, 4) for s in g["sockets"] if s["type"] == n)
        g["upright"] = carry.flat(np.array(r.sc["upright"]).reshape(4, 4) @ S0 @ np.linalg.inv(S1))


def torso_again(L, rel, sc, g, hide=()):
    """the torso joints its folder-mates have and `g` lacks, carried with turning; g is changed in place"""
    from kb import carry
    refs = L.mates("Chests", rel, g["scope"] if g["scope"] in ("folder", "maker") else "folder", hide)
    have = {s["type"] for s in g["sockets"]}; want = {n for r in refs for n in carry.joints("Chests", r.sc)} - have
    if not refs or not want: return g
    part = carry.Shape(L.lib + "/" + rel + ".stl", sc.get("scale", 1.0))
    g2 = carry.like("Chests", part, refs, stem=os.path.basename(rel), mode="rigid"); L.tidy([r for r in refs if r._shape is not None])
    for s in g2["sockets"]:
        if s["type"] in want:
            g["sockets"].append(s); g["how"][s["type"]] = g2["how"][s["type"]]; g["rejected"].pop(s["type"], None)
    for n in want:
        if n in g2["rejected"]: g["rejected"][n] = g2["rejected"][n] + " (also tried with turning)"
    g["again"] = sorted(want); set_upright(L, rel, g, hide)
    return g


def carry_part(L, cat, rel, sc, scopes=("folder", "maker"), hide=(), heads=None, mode=None):
    """-> {"scope", "method", "fits", "sockets", "how", "rejected", ["upright"]} for one part"""
    from kb import carry
    part = carry.Shape(L.lib + "/" + rel + ".stl", sc.get("scale", 1.0)); got, tried = None, {}
    for scope in scopes:
        refs = L.mates(cat, rel, scope, hide)
        if not refs: tried[scope] = "no fitted %s" % ("part beside it" if scope == "folder" else "part of this maker elsewhere"); continue
        g = carry.like(cat, part, refs, stem=os.path.basename(rel), mode=mode)
        L.tidy([r for r in refs if r._shape is not None])
        for n in [n for n, h in g["how"].items() if h["mode"] == "same" and h["match"] > SAME_REGION and (n in g["fits"] or any(s["type"] == n for s in g["sockets"]))]:
            g["rejected"][n] = "copied from its folder's frame, but the part's surface is %.2f mm off there (limit %.2f): not in that pose" % (g["how"][n]["match"], SAME_REGION)
            g["fits"].pop(n, None); g["sockets"] = [s for s in g["sockets"] if s["type"] != n]
        if cat == "Chests": g["sockets"] = [s for s in g["sockets"] if s["type"] in carry.TORSO and s["type"] not in g["rejected"]] + \
                                           [s for s in g["sockets"] if s["type"] not in carry.TORSO and not g["rejected"]]
        if cat == "Legs" and not g["fits"]: g["sockets"] = []
        g["scope"], g["method"] = scope, "like"
        if g["fits"] or g["sockets"]:
            if cat == "Chests": set_upright(L, rel, g, hide)
            got = g; break
        tried[scope] = "; ".join("%s: %s" % (n, w) if n != "*" else w for n, w in g["rejected"].items()) or "nothing carried"
        got = got or g
    if (got is None or not (got["fits"] or got["sockets"])) and cat == "Heads" and heads is not None:
        from kb import fit as KF
        Fn, m = heads.neck_fit(*KF.load(L.lib + "/" + rel + ".stl", sc.get("scale", 1.0)))
        g = {"scope": "rule", "method": "head", "fits": {}, "sockets": [], "how": {"Neck": {"mode": "head rule", "from": "MarFil Assault - Helmet 1", "match": round(m, 3), "whole": round(m, 3)}}, "rejected": {}}
        if m <= HEAD_MAX: g["fits"]["Neck"] = KF.flat(Fn); got = g
        else:
            tried["rule"] = "helmet 1's neck ring didn't match it (%.2f mm off)" % m
            got = got or g
    if got is None: got = {"scope": "-", "method": "-", "fits": {}, "sockets": [], "how": {}, "rejected": {}}
    got["tried"] = tried
    return got


def shard_of(A):
    i, n = (int(x) for x in opt(A, "--shard", "0/1").split("/")); return i, n
def done_rels(f):
    return {json.loads(l)["rel"] for l in open(f, encoding="utf-8")} if os.path.exists(f) else set()


def run(lib, work, A):
    types = opt(A, "--types", ",".join(TYPES)).split(","); i, n = shard_of(A); L = Lib(lib, work, types)
    out = "%s/run-%dof%d.jsonl" % (work, i, n); have = {g["rel"] for g in rows(work, "run")}      # whatever any shard has done
    todo = sorted((rel, cat, sc) for cat in types for rel, sc in L.P[cat] if not fitted(cat, sc) and rel not in have)[i::n]
    heads = None; t0 = time.time(); print("shard %d/%d: %d parts to do, %d done before" % (i, n, len(todo), len(have)), flush=True)
    with open(out, "a", encoding="utf-8") as fo:
        for k, (rel, cat, sc) in enumerate(todo):
            if cat == "Heads" and heads is None:
                from kb import fit as KF; heads = KF.Heads(lib)
            t1 = time.time()
            try: g = carry_part(L, cat, rel, sc, heads=heads)
            except Exception as e: g = {"scope": "-", "method": "error", "fits": {}, "sockets": [], "how": {}, "rejected": {"*": "%s: %s" % (type(e).__name__, e)}, "tried": {}}
            g.update(rel=rel, cat=cat, secs=round(time.time() - t1, 1)); fo.write(json.dumps(g) + "\n"); fo.flush()
            print("%4d/%d %-13s %-60s %s (%.0f s)" % (k + 1, len(todo), cat, os.path.basename(rel)[:60],
                  ("kept " + ", ".join(list(g["fits"]) + [s["type"] for s in g["sockets"]][:6]) + " [" + g["scope"] + "]") if g["fits"] or g["sockets"] else "none", g["secs"]), flush=True)
    print("shard %d done in %.0f s" % (i, time.time() - t0))


def again(lib, work, A):
    i, n = shard_of(A); L = Lib(lib, work, ["Chests"]); out = "%s/run-zz-%dof%d.jsonl" % (work, i, n)
    R = {g["rel"]: g for g in rows(work, "run")}; sc = dict(L.P["Chests"])
    todo = sorted(rel for rel, g in R.items() if g["cat"] == "Chests" and g["sockets"] and "again" not in g and g["scope"] in ("folder", "maker"))[i::n]
    print("shard %d/%d: %d torsos" % (i, n, len(todo)), flush=True)
    with open(out, "a", encoding="utf-8") as fo:
        for k, rel in enumerate(todo):
            t1 = time.time(); g = R[rel]; before = len(g["sockets"]); g.setdefault("again", [])
            try: torso_again(L, rel, sc[rel], g)
            except Exception as e: g["rejected"]["again"] = "%s: %s" % (type(e).__name__, e)
            fo.write(json.dumps(g) + "\n"); fo.flush()
            print("%4d/%d %-50s %d -> %d sockets: %s (%.0f s)" % (k + 1, len(todo), os.path.basename(rel)[:50], before, len(g["sockets"]), ", ".join(s["type"] for s in g["sockets"]), time.time() - t1), flush=True)


def loo(lib, work, A):
    from kb import carry
    types = opt(A, "--types", ",".join(TYPES)).split(","); i, n = shard_of(A); per = int(opt(A, "--per", "12")); scope = opt(A, "--scope", "folder")
    mode = opt(A, "--mode"); only = opt(A, "--maker")
    L = Lib(lib, work, types); out = "%s/loo-%s%s-%d.jsonl" % (work, scope, mode or "", i); have = done_rels(out); random.seed(11); todo = []
    for cat in types:
        bym = collections.defaultdict(list)
        for rel, sc in L.P[cat]:
            if fitted(cat, sc): bym[maker(rel)].append((rel, cat, sc))
        for m in sorted(bym):
            if not only or only in m: todo += random.sample(bym[m], min(per, len(bym[m])))
    todo = [t for k, t in enumerate(todo) if k % n == i and t[0] not in have]
    heads = None
    with open(out, "a", encoding="utf-8") as fo:
        for k, (rel, cat, sc) in enumerate(todo):
            t1 = time.time()
            if cat == "Heads" and scope == "rule" and heads is None:
                from kb import fit as KF; heads = KF.Heads(lib)
            g = carry_part(L, cat, rel, sc, scopes=() if scope == "rule" else (scope,), hide=(rel,), heads=heads, mode=mode)
            mine = dict(g["fits"]); mine.update({s["type"]: s["matrix"] for s in g["sockets"] if cat == "Chests"}); g["cmp"] = {}
            for name, (kind, T) in carry.joints(cat, sc).items():
                if name in mine:
                    X = np.array(mine[name]).reshape(4, 4)
                    g["cmp"][name] = [round(float(np.linalg.norm(carry.point(kind, X) - carry.point(kind, T))), 3), round(carry.ang(X, T), 2)]
                else: g["cmp"][name] = None
            if cat == "Legs" and g["fits"]:
                g["socks"] = []
                for s in g["sockets"]:
                    X = np.array(s["matrix"]).reshape(4, 4); tr = [np.array(o["matrix"]).reshape(4, 4) for o in sc.get("sockets") or [] if o["type"] == s["type"]]
                    if tr:
                        T = min(tr, key=lambda T: np.linalg.norm(T[:3, 3] - X[:3, 3])); g["socks"].append([s["type"], round(float(np.linalg.norm(T[:3, 3] - X[:3, 3])), 3), round(carry.ang(X, T), 2)])
            if "upright" in g and sc.get("upright"): g["up_deg"] = round(carry.ang(np.array(g["upright"]).reshape(4, 4), np.array(sc["upright"]).reshape(4, 4)), 2)
            g.update(rel=rel, cat=cat, secs=round(time.time() - t1, 1)); g.pop("sockets"); g.pop("fits"); fo.write(json.dumps(g) + "\n"); fo.flush()
            print("%4d/%d %-13s %-50s %s (%.0f s)" % (k + 1, len(todo), cat, os.path.basename(rel)[:50], "  ".join(
                "%s %s" % (nm, "dropped" if c is None else "%.2fmm %.1fdeg [%s %.2f]" % (c[0], c[1], g["how"][nm]["mode"], g["how"][nm]["match"])) for nm, c in g["cmp"].items()), g["secs"]), flush=True)


def rows(work, kind):
    out = []
    for f in sorted(glob.glob(glob.escape(work) + "/%s-*.jsonl" % kind)):
        out += [json.loads(l) for l in open(f, encoding="utf-8")]
    if kind == "run": out = list({g["rel"]: g for g in out}.values())       # a later file (run-zz-*: again) replaces a part's row
    return out


def report(work, kind):
    R = rows(work, kind); ok = lambda c: c[0] <= 0.5 and c[1] <= 3
    if kind.startswith("loo"):
        by = collections.defaultdict(list)
        for g in R:
            for n, c in g["cmp"].items(): by[(g["cat"], maker(g["rel"]), g["how"].get(n, {}).get("mode", "-"))].append((c, g["how"].get(n, {}).get("match"), g["rel"], n))
        print("leave-one-out (%s): joints kept / right (within 0.5 mm and 3 deg) / dropped" % kind)
        for cat in sorted({k[0] for k in by}):
            X = [x for k, v in by.items() if k[0] == cat for x in v]; K = [x for x in X if x[0]]
            print("%-13s %4d joints: kept %d, right %d, dropped %d%s" % (cat, len(X), len(K), sum(ok(x[0]) for x in K), len(X) - len(K),
                  "" if not K else "; kept: median %.2f, worst %.2f mm, %.1f deg" % (np.median([x[0][0] for x in K]), max(x[0][0] for x in K), max(x[0][1] for x in K))))
            for k in sorted(k for k in by if k[0] == cat):
                K = [x for x in by[k] if x[0]]
                print("     %-32s %-9s %3d: kept %3d, right %3d" % (k[1][:32], k[2], len(by[k]), len(K), sum(ok(x[0]) for x in K)))
            for x in X:
                if x[0] and not ok(x[0]): print("       WRONG %s %s: %.2f mm %.1f deg (match %.2f)" % (os.path.basename(x[2]), x[3], x[0][0], x[0][1], x[1]))
        S = [s for g in R for s in g.get("socks", [])]
        for t in sorted({s[0] for s in S}):
            X = [s for s in S if s[0] == t]; print("     legs' %-11s %3d: median %.2f, 90%% %.2f, worst %.2f mm; turn median %.1f, worst %.1f deg" % (
                t, len(X), np.median([x[1] for x in X]), np.quantile([x[1] for x in X], 0.9), max(x[1] for x in X), np.median([x[2] for x in X]), max(x[2] for x in X)))
        U = [g["up_deg"] for g in R if "up_deg" in g]
        if U: print("     torsos' upright: %d, median %.1f, worst %.1f deg" % (len(U), np.median(U), max(U)))
        return
    print("the unfitted parts: %d tried; kept = what POLICY uses" % len(R))
    for cat in sorted({g["cat"] for g in R}):
        X = [g for g in R if g["cat"] == cat]; K = [u for u in map(used, X) if u]
        print("%-13s %4d: got a fit / sockets %d (%s); none %d" % (cat, len(X), len(K), ", ".join("%s %d" % kv for kv in sorted(collections.Counter(g["scope"] for g in K).items())), len(X) - len(K)))
        if cat == "Chests":
            from kb import carry
            c = collections.Counter(len([s for s in g["sockets"] if s["type"] in carry.TORSO]) for g in K); print("       torso joints kept a part: %s" % dict(sorted(c.items())))
        for m in sorted({maker(g["rel"]) for g in X}):
            Xm = [g for g in X if maker(g["rel"]) == m]; print("     %-34s %4d: %4d" % (m[:34], len(Xm), sum(1 for g in Xm if used(g))))
    E = [g for g in R if g["method"] == "error"]
    for g in E[:10]: print("  error:", g["rel"], g["rejected"])


def merged(lib, g):
    """the part's sidecar with what was carried merged in -> (data, style, the bytes it had, what of Josh's stayed)"""
    from kb import sidecar
    p = lib + "/" + g["rel"] + ".sockets.json"; old, style = sidecar.load(p); base = open(p, "rb").read()
    new = {"fits": g["fits"], "sockets": g["sockets"], "notes": {}}
    if g.get("upright") and "upright" not in old: new["upright"] = g["upright"]
    for nm, h in g["how"].items():
        if nm in g["fits"] or any(s["type"] == nm for s in g["sockets"]):
            new["notes"][nm] = ("helmet 1's neck ring matched onto it (%.2f mm), Josh's Neck fit carried across (Nov 14)" % h["match"]) if g["method"] == "head" else \
                "carried from %s (%s, %s; Nov 14): region match %.2f mm, whole shape %.2f mm" % (h["from"], h["mode"], "its folder" if g["scope"] == "folder" else "same maker", h["match"], h["whole"])
    if not new["sockets"]: del new["sockets"]
    m, kept = sidecar.merge(new, old)
    return m, style, base, kept


def test(lib, work, A):
    """models for tests/creator/t_creator.py: each picked part on the Mar Fil body (a torso under the Mar Fil parts)"""
    import shutil
    from kb import sidecar
    sys.path.insert(0, REPO + "/kits/creator"); import add_creator as AC
    per = int(opt(A, "--per", "4")); R = [u for u in map(used, rows(work, "run")) if u]; L = Lib(lib, work, ["Chests"])
    for g in R:
        if g["cat"] == "Chests": set_upright(L, g["rel"], g)
    W = work + "/test"; NEW = W + "/worklib/NEW"; os.makedirs(NEW, exist_ok=True)
    ref = lambda k: lib + "/" + AC.REFS[k]
    body = [[ref("Torso 1"), "Chests", None], [ref("Legs 1A"), "Legs", "Waist"], [ref("Arm 1A R"), "Arms", "Shoulder R"], [ref("Arm 7B R"), "Arms", "Shoulder L"]]
    helmet = lib + "/Mar Fil - Tacticus/AssaultMarines-V2/Helmet-Heads/Heads/MarFil Assault - Helmet 1"
    models, nocut, check, picked = {}, [], [], []
    flat = {}
    def flat_torso(mk):                                     # a socketed torso of the maker with a Flat Waist, for flat legs
        if mk not in flat:
            flat[mk] = None
            for f in sorted(glob.glob(glob.escape(lib + "/" + mk) + "/**/Chests/*.sockets.json", recursive=True)):
                sc = json.load(open(f, encoding="utf-8-sig"))
                if any(s.get("type") == "Flat Waist" for s in sc.get("sockets") or []): flat[mk] = f[:-13].replace(os.sep, "/"); break
        return flat[mk]
    for cat in TYPES:
        X = sorted((g for g in R if g["cat"] == cat), key=lambda g: -max(h["match"] for n, h in g["how"].items() if n in g["fits"] or any(s["type"] == n for s in g["sockets"])))
        if not X: continue
        pick = X if len(X) <= 3 * per else X[:per // 2] + [X[(len(X) * (j + 1)) // (per - per // 2 + 1)] for j in range(per - per // 2)]
        for g in {g["rel"]: g for g in pick}.values():
            m, style, base, kept = merged(lib, g); nm = os.path.basename(g["rel"]); me = "NEW/" + nm
            shutil.copyfile(lib + "/" + g["rel"] + ".stl", NEW + "/" + nm + ".stl"); sidecar.save(NEW + "/" + nm + ".sockets.json", m, style)
            key = next(iter(g["fits"]), None); types = [s["type"] for s in g["sockets"]]
            if cat == "Arms":
                if key not in ("Shoulder R", "Shoulder L"): continue
                mod = [body[0], body[1], [me, "Arms", key]]; nocut.append(nm)
            elif cat == "Legs":
                nocut.append(nm)
                if key == "Waist": mod = [body[0], [me, "Legs", "Waist"], body[2], body[3]]
                else:
                    host = flat_torso(maker(g["rel"]))
                    if not host: print("  %s: no torso with a Flat Waist socket to stand it under" % nm); continue
                    mod = [[host, "Chests", None], [me, "Legs", key]]
            elif cat == "Chests":
                mod = [[me, "Chests", None]]
                for t, part in (("Waist", body[1]), ("Shoulder R", body[2]), ("Shoulder L", body[3]), ("Neck", [helmet, "Heads", "Neck"])):
                    if t in types: mod.append(part)
                check += [os.path.basename(q[0]) for q in mod[1:]]; nocut += [os.path.basename(q[0]) for q in mod[1:]]
            elif cat == "Heads": mod = body + [[me, "Heads", "Neck"]]
            else: mod = body + [[me, "Shoulder Pads", key]]
            models["%s%d" % (cat[:2].lower(), len(models) + 1)] = mod; picked.append((cat, g))
    job = {"worklib": W + "/worklib", "tiow": None, "out": W + "/out", "new": "NEW/", "models": models, "nocut": sorted(set(nocut)), "check": sorted(set(check))}
    json.dump(job, open(W + "/job.json", "w"), indent=0)
    json.dump([[c, g["rel"], g["scope"], g["how"]] for c, g in picked], open(W + "/picked.json", "w"), indent=0)
    print("test: %d models -> %s/job.json" % (len(models), W))
    r = AC.run_bpy(REPO + "/tests/creator/t_creator.py", W + "/job.json", addons=True)
    print("\n".join(l for l in (r.stdout or "").splitlines() if l.startswith(("  ok", "  FAIL", "      ")) or "passed" in l or "fail" in l.lower()))
    if r.returncode: print((r.stderr or "")[-1500:])


def build(lib, work, task):
    from kb import sidecar, deliver, index as kbindex
    R = [u for u in map(used, rows(work, "run")) if u]; D = deliver.Delivery(task, work + "/deliver"); n = 0; L = Lib(lib, work, ["Chests"])
    for g in R:
        if g["cat"] == "Chests": set_upright(L, g["rel"], g)
    ip = lib + "/_builder/index.json"; raw = open(ip, "rb").read(); IX = kbindex.Index(raw); missing = []
    types = json.load(open(REPO + "/joints.json", encoding="utf-8")); log = []
    for g in sorted(R, key=lambda g: g["rel"]):
        m, style, base, kept = merged(lib, g)
        bad = sidecar.problems(m, None)
        if bad: print("NOT written (%s): %s" % (bad[:2], g["rel"])); continue
        D.replace("lib", g["rel"] + ".sockets.json", sidecar.dumps(m, style), deliver.md5b(base)); n += 1
        ipath = g["rel"].replace("/", "\\") + ".stl"
        if ipath in IX.by_path: IX.update_part(ipath, m)
        else: missing.append(ipath)
        log.append("%s\t%s\t%s\t%s" % (g["cat"], g["scope"], ",".join(list(g["fits"]) + [s["type"] for s in g["sockets"]]), g["rel"]))
    D.replace("lib", "_builder/index.json", IX.dumps(), deliver.md5b(raw))
    nf = lib + "/_builder/no_fit.txt"
    if os.path.exists(nf):                                # the parts that now have a fit leave the page's list
        b = open(nf, "rb").read(); gone = {g["rel"].replace("/", "\\") + ".stl" for g in R if g["fits"]}
        keep = [l for l in b.split(b"\n") if l.rstrip(b"\r").decode("utf-8", "replace").split("\t")[-1] not in gone]
        if len(keep) != len(b.split(b"\n")): D.replace("lib", "_builder/no_fit.txt", b"\n".join(keep), deliver.md5b(b)); print("no_fit.txt: %d lines leave" % (len(b.split(b"\n")) - len(keep)))
    D.build(); open(work + "/fitted.tsv", "w", encoding="utf-8", newline="\n").write("\n".join(log) + "\n")
    print("delivery %s: %d sidecars, the index (%d of them not in it: %s)" % (task, n, len(missing), missing[:3]))


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if not A: sys.exit(__doc__)
    cmd = A[0]
    if cmd == "shapes": shapes(A[1], A[2], A)
    elif cmd == "ext": ext(A[1], A[2], opt(A, "--types", ",".join(TYPES)).split(","))
    elif cmd == "run": run(A[1], A[2], A)
    elif cmd == "loo": loo(A[1], A[2], A)
    elif cmd == "again": again(A[1], A[2], A)
    elif cmd == "report": report(A[1], A[2] if len(A) > 2 else "run")
    elif cmd == "test": test(A[1], A[2], A)
    elif cmd == "build": build(A[1], A[2], A[3])
    else: sys.exit(__doc__)
