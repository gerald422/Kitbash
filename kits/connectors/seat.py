"""Seat a maker's parts by Josh's connectors (notes 100): Blender in the background, no Claude.

    "Seat connectors.bat"            search, open the report, answer Y to write (or N: nothing written)
    "Seat connectors.bat" restore    put back what the last run wrote (its backup), or: restore TASK
    "Seat connectors.bat" write      write the last run that was searched but not written (no new search)

    BL kits/connectors/seat.py -- run CONFIG [--lib LIB] [--only TEXT] [--list FILE] [--types Arms,Legs] [--workers N] [--yes] [--dry] [--sure]
    BL kits/connectors/seat.py -- write [TASK] [--lib LIB] [--yes] [--sure] [--near MM]   (--sure: sure fits only; --near:
                                    only fits within MM and 10 deg of the old fit)
    BL kits/connectors/seat.py -- restore [TASK] [--lib LIB]
  BL = blender --background --factory-startup --python

1. The connectors are read from Josh's blends (CONFIG, e.g. kits/connectors/marfil.json), each checked to still sit on
   its reference part; pad insides are cut from his placed pads (the pad's triangles resting on his spot shell).
2. Every part of the maker in those types is searched (kb.connect.find_all) by WORKERS Blender processes. The shape
   sets the place and tilt; the turn of a round connector (the disc: an arm's swing) is kept from the part's own fit
   (the file's frame when it has none), and a variant (look) match keeps the old place when that fits as well.
3. _backups/<task>/report.txt (opened) and plan.json: per part sure / look / none, and how far the new fit moves it.
4. On Y: each sidecar and the page index are backed up to _backups/<task>/before, the new fit merged in
   (kb.sidecar.merge: fits Josh fixed by hand, "exact", stay), sockets a part has none of added (sure only), the
   page index refreshed for those parts. sure = written; look = written, noted in the sidecar, listed to check;
   none = left as it is, listed by connector (= what to cut next).
Reference parts, variants (mirrored copies inside a sidecar) and connectors that are on both sides (shin spot) are
searched but not written."""
import sys, os, json, time, subprocess, shutil, hashlib, struct
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, REPO)
from kb import sidecar as SC, origin as OG

LIB = "D:/Kitbash Library"
MX = np.diag([-1.0, 1, 1, 1])
GAP = 0.3                 # mm: a pad's inside = its triangles within this of Josh's spot shell (they rest at 0.07-0.08)
ON_REF = 0.005            # mm: a connector must sit on its reference part within this (median, point to plane)


def opt(A, n, d=None): return A[A.index(n) + 1] if n in A else d
def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()
def flat(M): return [round(float(x), 6) for x in np.asarray(M).reshape(-1)]
def mat(m): return np.array(m, float).reshape(4, 4)


def maker(path):
    """(the sidecar in the maker's file coordinates, G, G inverse): a part whose origin was moved onto its joint
    (origins.py, notes 101) is searched as the maker exported it, where Josh's connectors were cut and where a kit's
    parts share one frame; G takes those coordinates to the file as it is now (None for a part never moved)"""
    sc = json.load(open(path, encoding="utf-8-sig")); g = OG.from_file(sc)
    if not g: return sc, None, None
    G = mat(g); return OG.maker_view(sc), G, np.linalg.inv(G)


def unmoved(tri, back): return tri if back is None else tri @ back[:3, :3].T + back[:3, 3]


def write_stl(T, out):
    with open(out, "wb") as f:
        f.write(b"\0" * 80); f.write(struct.pack("<I", len(T)))
        for t in T:
            n = np.cross(t[1] - t[0], t[2] - t[0]); l = np.linalg.norm(n); n = n / l if l else n
            f.write(struct.pack("<12fH", *n, *np.asarray(t).reshape(-1), 0))


def parts(lib, maker, types):
    """[(cat, rel without suffix, sidecar)] for the maker's parts of these types"""
    out = []
    for d, dn, fs in os.walk(os.path.join(lib, maker)):
        dn[:] = sorted(x for x in dn if not x.startswith("_"))
        for f in sorted(fs):
            if not f.endswith(SC.SUFFIX) or not os.path.exists(os.path.join(d, f[:-len(SC.SUFFIX)] + ".stl")): continue
            try: sc = json.load(open(os.path.join(d, f), encoding="utf-8-sig"))
            except ValueError: continue
            if sc.get("category") in types:
                out.append((sc["category"], os.path.relpath(os.path.join(d, f[:-len(SC.SUFFIX)]), lib).replace("\\", "/"), sc))
    return out


def side_fit(sc, base):
    """(the fit named base as on a right part, its side 'R' / 'L' / None) or (None, side) when it has none"""
    fits = sc.get("fits") or {}
    if base in fits: return mat(fits[base]), None
    if base + " R" in fits: return mat(fits[base + " R"]), "R"
    if base + " L" in fits: return MX @ mat(fits[base + " L"]) @ MX, "L"
    return None, None


def side_sock(sc, typ):
    """the socket typ (an unsided one such as Back as it is; else R, else L mirrored to R) or None"""
    for s in sc.get("sockets") or []:
        if s.get("type") == typ: return mat(s["matrix"])
    for s in sc.get("sockets") or []:
        if s.get("type") == typ + " R": return mat(s["matrix"])
    for s in sc.get("sockets") or []:
        if s.get("type") == typ + " L": return MX @ mat(s["matrix"]) @ MX
    return None


def part_side(rel, sc, base, sided):
    if not sided: return None
    fits = sc.get("fits") or {}
    if base + " R" in fits: return "R"
    if base + " L" in fits: return "L"
    return "L" if rel.endswith(" L") or "/Left/" in rel else "R"


# ---------------------------------------------------------------- 1. connectors from Josh's blends (bpy)
def read_connectors(cfg, lib, work):
    import bpy, bmesh
    from kb import connect as C
    blends = os.path.expanduser(cfg.get("blends") or ""); os.makedirs(work + "/conn", exist_ok=True); bad = []

    def tris(ob):
        bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces)
        T = np.array([[list(v.co) for v in f.verts] for f in bm.faces]); bm.free(); return T

    opened = None
    for cat, cons in cfg["types"].items():
        for c in cons:
            if c.get("blend"):                    # (a placed connector whose spot is a library part needs no blend)
                p = os.path.join(blends, c["blend"])
                if opened != p: bpy.ops.wm.open_mainfile(filepath=p, load_ui=False); opened = p
            obs = bpy.data.objects
            if "pad" in c:                        # the pad's inside: what of the placed pad rests on the spot shell
                if c["pad"] not in obs or c["spot"] not in obs: bad.append("%s: %s or %s not in %s" % (c["name"], c["pad"], c["spot"], c["blend"])); continue
                pad = obs[c["pad"]]; T = tris(pad); Mw = np.array(pad.matrix_world)
                spot = C.Surface(tris(obs[c["spot"]]), spacing=0.03)
                Tw = T @ Mw[:3, :3].T + Mw[:3, 3]; T = T[spot.dist(Tw.mean(1))[1] < GAP]
            elif "placed" in c:                   # RETIRED Nov 16 (docs/PLAN.md): not for placing. The same from a part placed by its LIBRARY fit on the reference arm's socket
                if "spot" in c and c["spot"] not in obs: bad.append("%s: %s not in %s" % (c["name"], c["spot"], c["blend"])); continue
                ra, _, rb = maker(lib + "/" + c["on"] + SC.SUFFIX); S = side_sock(ra, c["socket"])  # (a weapon's hand on the wrist:
                ws, _, wb = maker(lib + "/" + c["placed"] + SC.SUFFIX); F, fs = side_fit(ws, c["fit"])  #  notes 104)
                if S is None or F is None: bad.append("%s: no %s socket on %s or no %s fit on %s" % (c["name"], c["socket"], c["on"], c["fit"], c["placed"])); continue
                T = unmoved(C.soup(lib + "/" + c["placed"] + ".stl", ws.get("scale", 1.0)), wb); P = S @ F
                if fs == "L": T = (T * np.array([-1.0, 1, 1]))[:, [0, 2, 1]]; c["mirrored"] = True   # fitted for the left only: its mirror
                                                  # image is placed (F is the fit as on a right part), as the search mirrors a left part
                if "spot" in c: spot = C.Surface(tris(obs[c["spot"]]), spacing=0.03)
                else:                             # no cut: the "on" part's own surface within spot_mm of its socket (a backpack
                    O = unmoved(C.soup(lib + "/" + c["on"] + ".stl", ra.get("scale", 1.0)), rb)   # on the torso's back, notes 107)
                    spot = C.Surface(O[np.linalg.norm(O.mean(1) - S[:3, 3], axis=1) < float(c.get("spot_mm", 25))], spacing=0.05)
                X = (T @ P[:3, :3].T + P[:3, 3]).mean(1); i = np.arange(len(T))
                if "spot" not in c: i = i[np.linalg.norm(X - S[:3, 3], axis=1) < float(c.get("spot_mm", 25)) + 3.0]   # (only these can touch it)
                T = T[i[spot.dist(X[i])[1] < float(c.get("gap", GAP))]] if len(i) else T[:0]
            else:
                if c["object"] not in obs: bad.append("%s: %s not in %s" % (c["name"], c["object"], c["blend"])); continue
                T = tris(obs[c["object"]])
            if len(T) < 20: bad.append("%s: only %d triangles" % (c["name"], len(T))); continue
            rs, Gr, back = maker(lib + "/" + c["ref"] + SC.SUFFIX); now = C.soup(lib + "/" + c["ref"] + ".stl", rs.get("scale", 1.0))
            ref = C.Surface(unmoved(now, back), mirror=bool(c.get("mirrored"))); con = C.Connector(T, c["name"])
            m = float(np.median(ref.dist(con.fine)[0]))
            if m > ON_REF and back is not None and float(np.median(C.Surface(now).dist(con.fine)[0])) <= ON_REF:
                T = unmoved(T, back); con = C.Connector(T, c["name"]); m = float(np.median(ref.dist(con.fine)[0]))   # cut on the moved file
            if m > ON_REF: bad.append("%s: %.4f mm off its reference part %s (moved in the blend?)" % (c["name"], m, c["ref"])); continue
            out = "%s/conn/%s__%s.stl" % (work, cat, c["name"].replace(" ", "_")); write_stl(T, out); c["stl"] = out
            print("  connector %-16s %-14s %6d triangles, on its reference at %.4f mm" % (c["name"], cat, len(T), m), flush=True)
    return bad


# ---------------------------------------------------------------- 2. the search (a worker, bpy for the KD tree)
def at_fit(C, con, surf, N):
    """config "near_first" (hands.py's rounds, notes 108): a part that has a fit for the joint is not searched from
    scratch. The connector is settled where that fit puts it, and at its three half turns about its own axes there (a
    library fit that holds the hand the other way round: the flipped Bladeguard swords, notes 105); the best is
    chosen as find() does. So a round over a maker costs seconds a part, not a minute; a part whose fit is far out
    another way reads as none (it would not be written under --near anyway). Parts with no fit are searched in full."""
    w, v = np.linalg.eigh(np.cov((con.surf.S - con.c).T)); out = []
    for ax in (None, v[:, 0], v[:, 1], v[:, 2]):
        R = N[:3, :3] if ax is None else N[:3, :3] @ C._rot(ax, 180.0)
        out.append(C._result(*C.settle(con, surf, R, N[:3, :3] @ con.c + N[:3, 3] - R @ con.c)))
    return dict(C.choose(con, surf, out, near=N), at_fit=True)


def search(cfgp, lib, work, i, n):
    from kb import connect as C, geo
    cfg = json.load(open(cfgp, encoding="utf-8")); jobs = json.load(open(work + "/jobs.json", encoding="utf-8"))[i::n]
    setup = {}
    for cat, cons in cfg["types"].items():
        L = []
        for c in cons:
            rs = maker(lib + "/" + c["ref"] + SC.SUFFIX)[0]
            info = dict(c, con=C.Connector.from_stl(c["stl"], c["name"]))
            if "fit" in c:
                F, s = side_fit(rs, c["fit"]); info.update(F_ref=F, sided=s is not None)
            else: info.update(S_ref=side_sock(rs, c["socket"]))
            L.append(info)
        setup[cat] = L
    out = open("%s/res_%d.jsonl" % (work, i), "a", encoding="utf-8")
    for cat, rel in jobs:
        t0 = time.time(); L = setup[cat]; sc, Gp, back = maker(lib + "/" + rel + SC.SUFFIX)
        now = (lambda F: F) if back is None else (lambda F: F @ back)           # a fit found in the maker's frame, for the file as it is now
        fc = next(x for x in L if "fit" in x); side = part_side(rel, sc, fc["fit"], fc["sided"]); left = side == "L"
        try: tri = unmoved(C.soup(lib + "/" + rel + ".stl", sc.get("scale", 1.0)), back); surf = C.Surface(tri, mirror=left)
        except (OSError, ValueError) as e:
            out.write(json.dumps({"cat": cat, "rel": rel, "error": str(e)}) + "\n"); out.flush(); continue
        # where the part's own fit / sockets put each connector: the turn to keep among equals (a round connector
        # doesn't fix the arm's swing; the library's fit does), and the pose a variant (look) match stays at
        near = {}
        for x in L:
            if "fit" in x and x.get("F_ref") is not None:
                Fo, _ = side_fit(sc, x["fit"])
                if Fo is not None: near[x["name"]] = np.linalg.inv(Fo) @ x["F_ref"]
            elif "socket" in x and x.get("S_ref") is not None:
                So = side_sock(sc, x["socket"])
                if So is not None: near[x["name"]] = So @ np.linalg.inv(x["S_ref"])
        if cfg.get("near_first") and len(L) == 1 and L[0]["name"] in near: found = {L[0]["name"]: at_fit(C, L[0]["con"], surf, near[L[0]["name"]])}
        else: found = C.find_all([x["con"] for x in L], surf, near=near)
        for x in L:
            f = found[x["name"]]; N = near.get(x["name"])
            if N is not None and f["level"] == "look":         # a variant: keep the old place if it fits as well (no flips)
                r0 = C._result(*C.settle(x["con"], surf, N[:3, :3], N[:3, 3]))
                if r0["level"] != "none" and r0["match"] <= f["match"] + C.TIE:
                    found[x["name"]] = dict(r0, ambiguous=f.get("ambiguous"), turned=0.0, kept_old=True)
        r = {"cat": cat, "rel": rel, "side": side, "found": {}, "sockets": [], "secs": round(time.time() - t0, 1)}
        V = tri.reshape(-1, 3)[::7]
        for x in L:
            f = found[x["name"]]
            r["found"][x["name"]] = {k: f.get(k) for k in ("level", "match", "cover", "ambiguous", "turned", "round", "kept_old")}
            if f["level"] == "none": continue
            M = f["M"]
            if "fit" in x and x.get("F_ref") is not None:
                Fr = x["F_ref"] @ np.linalg.inv(M); key = x["fit"] + (" " + side if x["sided"] else "")
                F = MX @ Fr @ MX if left else Fr; old = (sc.get("fits") or {}).get(key)
                fit = {"key": key, "matrix": flat(now(F)), "level": f["level"], "connector": x["name"],
                       "match": f["match"], "cover": f["cover"], "ambiguous": bool(f.get("ambiguous")),
                       "exact": key in (sc.get("exact") or []), "had": old is not None}
                if old is not None:
                    O = mat(old); fit["moved_mm"] = round(float(np.median(np.linalg.norm((V @ F[:3, :3].T + F[:3, 3]) - (V @ O[:3, :3].T + O[:3, 3]), axis=1))), 2)
                    fit["turn_deg"] = round(geo.ang(F[:3, :3] @ O[:3, :3].T), 1)
                r["fit"] = fit
            elif "socket" in x and x.get("S_ref") is not None and not x.get("both_sides"):
                typ = x["socket"] + " " + (side or "R"); Sr = M @ x["S_ref"]; S = MX @ Sr @ MX if left else Sr
                r["sockets"].append({"type": typ, "matrix": flat(S if Gp is None else Gp @ S), "level": f["level"], "connector": x["name"],
                                     "has": any(s.get("type") == typ for s in sc.get("sockets") or [])})
        out.write(json.dumps(r) + "\n"); out.flush()
    print("worker %d done: %d parts" % (i, len(jobs)), flush=True)


# ---------------------------------------------------------------- 3. the report
def report(cfg, task, plan, secs):
    fits = [p for p in plan if p.get("fit")]; W = []
    w = W.append
    sure = [p for p in fits if p["fit"]["level"] == "sure" and not p["fit"]["exact"]]
    look = [p for p in fits if p["fit"]["level"] == "look" and not p["fit"]["exact"]]
    exact = [p for p in fits if p["fit"]["exact"]]
    none = [p for p in plan if not p.get("fit") and not p.get("error")]
    socks = [(p, s) for p in plan for s in p.get("sockets", []) if not s["has"] and s["level"] == "sure"]
    nm = lambda p: p["rel"].split("/", 1)[1]
    w("Seat connectors: %s  (task %s, %d parts searched in %.0f min)" % (cfg["maker"], task, len(plan), secs / 60))
    w("")
    w("Will write: %d fits (%d sure, %d look), and %d sockets parts had none of." % (len(sure) + len(look), len(sure), len(look), len(socks)))
    w("Left as they are: %d parts no connector was found on, %d fits Josh fixed by hand (exact), %d unreadable." % (
        len(none), len(exact), sum(1 for p in plan if p.get("error"))))
    for cat in cfg["types"]:
        c = [p for p in plan if p["cat"] == cat]
        w("  %-14s %3d parts: sure %3d, look %3d, none %3d" % (cat, len(c), sum(p in sure for p in c), sum(p in look for p in c), sum(p in none for p in c)))
    w(""); w("== LOOK: written, check these by eye (most moved first; legs may need turning round) ==")
    for p in sorted(look, key=lambda p: -(p["fit"].get("moved_mm") or 0)):
        f = p["fit"]; w("  %-62s %-11s %.4f mm %3.0f%%  %s%s" % (nm(p)[:62], f["key"], f["match"], 100 * f["cover"],
          "moved %.1f mm / %.0f deg" % (f["moved_mm"], f["turn_deg"]) if f["had"] else "had no fit", "  (fits elsewhere too)" if f["ambiguous"] else ""))
    big = [p for p in sure if p["fit"]["had"] and (p["fit"]["moved_mm"] > 1.0 or p["fit"]["turn_deg"] > 5)]
    w(""); w("== SURE but moved more than 1 mm or 5 deg from the old fit (%d): the old fit or the kit's turn differs ==" % len(big))
    for p in sorted(big, key=lambda p: -p["fit"]["moved_mm"]):
        f = p["fit"]; w("  %-62s %-11s moved %.1f mm / %.0f deg" % (nm(p)[:62], f["key"], f["moved_mm"], f["turn_deg"]))
    new = [p for p in sure + look if not p["fit"]["had"]]
    w(""); w("== Parts that had no fit and get one (%d) ==" % len(new))
    for p in new: w("  %-62s %-11s %s" % (nm(p)[:62], p["fit"]["key"], p["fit"]["level"]))
    w(""); w("== Sockets added (the part had none of that type) (%d) ==" % len(socks))
    for p, s in socks: w("  %-62s %s (%s)" % (nm(p)[:62], s["type"], s["connector"]))
    w(""); w("== NONE: no connector found, left as they are (%d): a connector to cut, by kit ==" % len(none))
    by = {}
    for p in none: by.setdefault((p["cat"], p["rel"].split("/")[1]), []).append(p)
    for (cat, kit), ps in sorted(by.items()):
        w("  %s, %s: %d   (%s)" % (cat, kit, len(ps), ", ".join(os.path.basename(p["rel"]).replace("MarFil ", "") for p in ps[:6]) + (" ..." if len(ps) > 6 else "")))
    if exact:
        w(""); w("== Fixed by hand (exact), kept ==")
        for p in exact: w("  %-62s %s (found %s)" % (nm(p)[:62], p["fit"]["key"], p["fit"]["level"]))
    errs = [p for p in plan if p.get("error")]
    if errs:
        w(""); w("== Unreadable ==")
        for p in errs: w("  %s: %s" % (nm(p), p["error"]))
    return "\r\n".join(W) + "\r\n", sure + look, socks


# ---------------------------------------------------------------- 4. writing, with backups
def write(lib, task_dir, todo, socks):
    from kb.index import Index
    B = task_dir + "/before"; wrote = {}; skipped = []
    by = {}
    for p in todo: by.setdefault(p["rel"], {"p": p, "socks": []})
    for p, s in socks: by.setdefault(p["rel"], {"p": p, "socks": []})["socks"].append(s)
    day = time.strftime("%b %d").replace(" 0", " ")
    for rel, e in by.items():
        p = e["p"]; path = lib + "/" + rel + SC.SUFFIX; old, style = SC.load(path); new = {"sockets": []}
        f = p.get("fit")
        if f and not f["exact"] and f["level"] in ("sure", "look"):
            new["fits"] = {f["key"]: f["matrix"]}
            new["notes"] = {f["key"]: "connector %s, %s (%.4f mm, %.0f%% on), seat.py %s%s" % (
                f["connector"], f["level"], f["match"], 100 * f["cover"], day, ": LOOK, check by eye" if f["level"] == "look" else "")}
        for s in e["socks"]:
            new["sockets"].append({"type": s["type"], "name": "%s_socket_%s" % (old.get("part") or os.path.basename(rel), s["type"]),
                                   "matrix": s["matrix"], "props": {"tiow_from": "connector %s (seat.py %s)" % (s["connector"], day)}})
        if not new["sockets"]: del new["sockets"]
        merged, kept = SC.merge(new, old); was = SC.problems(old)
        bad = [x for x in SC.problems(merged) if x not in was]        # only what this merge would break (32 Mar Fil pads lack schemaVersion)
        if bad: skipped.append("%s: %s" % (rel, bad[:2])); continue
        b = B + "/" + rel + SC.SUFFIX
        if not os.path.exists(b): os.makedirs(os.path.dirname(b), exist_ok=True); shutil.copyfile(path, b)
        SC.save(path, merged, style); wrote[rel] = md5(path)
    ip = lib + "/_builder/index.json"; idx_note = ""
    try:
        idx = Index.load(ip)
        if not os.path.exists(B + "/_builder/index.json"): os.makedirs(B + "/_builder", exist_ok=True); shutil.copyfile(ip, B + "/_builder/index.json")
        n = 0
        for rel in wrote:
            k = rel.replace("/", "\\") + ".stl"
            if k in idx.by_path: idx.update_part(k, SC.load(lib + "/" + rel + SC.SUFFIX)[0]); n += 1
        open(ip, "wb").write(idx.dumps()); idx_note = "page index: %d parts refreshed" % n
    except (ValueError, OSError) as ex: idx_note = "page index NOT refreshed (%s): run Prepare" % ex
    json.dump({"wrote": wrote, "index": md5(ip) if os.path.exists(ip) else None}, open(task_dir + "/written.json", "w", encoding="utf-8"), indent=1)
    return wrote, skipped, idx_note


def restore(lib, task):
    from kb.index import Index
    root = lib + "/_backups"
    if not task:
        ts = sorted((d for d in os.listdir(root) if d.startswith("connectors-") and os.path.exists(root + "/" + d + "/written.json")),
                    key=lambda d: os.path.getmtime(root + "/" + d + "/written.json"))
        if not ts: print("no seat.py run to restore"); return
        task = ts[-1]
    T = root + "/" + task; WJ = json.load(open(T + "/written.json", encoding="utf-8")); W = WJ["wrote"]
    print("restore %s: %d sidecars" % (task, len(W)))
    if input("Put them back as they were before that run? [y/N] ").strip().lstrip(chr(0xfeff)).lower() not in ("y", "yes"): print("nothing changed"); return
    back, changed = [], []
    for rel, m in W.items():
        path = lib + "/" + rel + SC.SUFFIX
        if os.path.exists(path) and md5(path) != m: changed.append(rel); continue          # saved since (Josh's correction): keep
        shutil.copyfile(T + "/before/" + rel + SC.SUFFIX, path); back.append(rel)
    ip = lib + "/_builder/index.json"; ib = T + "/before/_builder/index.json"
    if not changed and os.path.exists(ib) and os.path.exists(ip) and md5(ip) == WJ.get("index"):   # untouched since: the old file itself
        shutil.copyfile(ib, ip); note = "page index put back"
    else:
      try:
        idx = Index.load(ip)
        for rel in back:
            k = rel.replace("/", "\\") + ".stl"
            if k in idx.by_path: idx.update_part(k, SC.load(lib + "/" + rel + SC.SUFFIX)[0])
        open(ip, "wb").write(idx.dumps()); note = "page index refreshed"
      except (ValueError, OSError) as ex: note = "page index NOT refreshed (%s): run Prepare" % ex
    cb = T + "/before/_builder/cut_only.json"
    if os.path.exists(cb): shutil.copyfile(cb, lib + "/_builder/cut_only.json"); note += "; cut-only list put back (run Prepare)"
    print("put back %d; %d changed since that run, left as they are%s; %s" % (len(back), len(changed), (": " + ", ".join(changed[:5])) if changed else "", note))
    with open(T + "/restored.txt", "a", encoding="utf-8") as f: f.write("%s: put back %d, kept %d\n" % (time.strftime("%Y-%m-%d %H:%M"), len(back), len(changed)))


# ---------------------------------------------------------------- the run
def run(cfgp, A):
    import bpy
    lib = opt(A, "--lib", LIB); cfg = json.load(open(cfgp, encoding="utf-8"))
    types = opt(A, "--types").split(",") if opt(A, "--types") else list(cfg["types"])
    cfg["types"] = {k: v for k, v in cfg["types"].items() if k in types}
    n = int(opt(A, "--workers", max(1, min(12, (os.cpu_count() or 4) - 2)))); only = opt(A, "--only")
    task = "connectors-" + time.strftime("%Y-%m-%d"); k = 1
    while True:                                    # (two runs at once, hands.py for two makers, never share a folder)
        T = lib + "/_backups/" + task
        try: os.mkdir(T); break
        except FileExistsError: k += 1; task = "connectors-%s-%d" % (time.strftime("%Y-%m-%d"), k)
    work = T + "/work"; os.makedirs(work)
    t0 = time.time(); print("%s: reading Josh's connectors from %s" % (task, cfg.get("blends") or "(none: placed parts only)"), flush=True)
    bad = read_connectors(cfg, lib, work)
    if bad: print("\nSTOPPED, a connector isn't right:\n  " + "\n  ".join(bad)); return
    json.dump(cfg, open(work + "/config.json", "w", encoding="utf-8"), indent=1)
    refs = {c["ref"] for cons in cfg["types"].values() for c in cons}
    keep = set(open(opt(A, "--list"), encoding="utf-8").read().splitlines()) if opt(A, "--list") else None      # --list FILE: these library paths only
    P = [(c, r) for c, r, sc in parts(lib, cfg["maker"], list(cfg["types"])) if r not in refs and (not only or only in r) and (keep is None or r in keep)]
    order = {c: i for i, c in enumerate(cfg["types"])}; P.sort(key=lambda x: (order[x[0]], x[1]))
    json.dump(P, open(work + "/jobs.json", "w", encoding="utf-8"))
    n = max(1, min(n, len(P))); print("searching %d parts (%s) with %d Blender workers..." % (len(P), ", ".join(cfg["types"]), n), flush=True)
    procs = [subprocess.Popen([bpy.app.binary_path, "--background", "--factory-startup", "--python", os.path.abspath(__file__), "--",
                               "search", work + "/config.json", lib, work, str(i), str(n)],
                              stdout=open("%s/worker_%d.log" % (work, i), "w"), stderr=subprocess.STDOUT) for i in range(n)]
    last = -1
    while any(p.poll() is None for p in procs):
        time.sleep(10)
        done = sum(sum(1 for _ in open(f, encoding="utf-8")) for f in (work + "/res_%d.jsonl" % i for i in range(n)) if os.path.exists(f))
        if done != last: print("  %d of %d parts, %.0f min" % (done, len(P), (time.time() - t0) / 60), flush=True); last = done
    plan = [json.loads(l) for i in range(n) if os.path.exists(work + "/res_%d.jsonl" % i) for l in open(work + "/res_%d.jsonl" % i, encoding="utf-8")]
    if len(plan) < len(P): print("!! %d parts not searched (a worker stopped): see %s/worker_*.log" % (len(P) - len(plan), work))
    json.dump(plan, open(T + "/plan.json", "w", encoding="utf-8"), indent=0)
    text, todo, socks = report(cfg, task, plan, time.time() - t0)
    open(T + "/report.txt", "wb").write(text.encode("utf-8"))
    if "--dry" in A:
        print("\n" + text.split("\r\n== LOOK")[0].replace("\r\n", "\n")); print("The full list: %s/report.txt" % T)
        print("dry run: nothing written (\"Seat connectors.bat\" write  writes it later)"); return
    ask_and_write(lib, T, text, todo, socks, A)


def write_task(lib, task, A):
    """write a run that was searched but not written (a dry run, or one answered N)"""
    root = lib + "/_backups"
    if not task:
        ts = sorted((d for d in os.listdir(root) if d.startswith("connectors-") and os.path.exists(root + "/" + d + "/plan.json")
                     and not os.path.exists(root + "/" + d + "/written.json")), key=lambda d: os.path.getmtime(root + "/" + d + "/plan.json"))
        if not ts: print("no searched run left to write: run \"Seat connectors.bat\""); return
        task = ts[-1]
    T = root + "/" + task
    if os.path.exists(T + "/written.json"): print("%s was written already" % task); return
    cfg = json.load(open(T + "/work/config.json", encoding="utf-8")); plan = json.load(open(T + "/plan.json", encoding="utf-8"))
    print("%s, searched %s" % (task, time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(T + "/plan.json")))))
    text, todo, socks = report(cfg, task, plan, 0); ask_and_write(lib, T, text, todo, socks, A)


def ask_and_write(lib, T, text, todo, socks, A):
    print("\n" + text.split("\r\n== LOOK")[0].replace("\r\n", "\n")); print("The full list: %s/report.txt" % T)
    if "--sure" in A:          # look matches left as they are (another design of the connector: Veteran necks, notes 102)
        n = len(todo); todo = [p for p in todo if p["fit"]["level"] == "sure"]
        print("--sure: writing the %d sure fits only; %d look fits left as they are" % (len(todo), n - len(todo)))
    if "--near" in A:          # only fits within MM (and 10 deg) of the part's old fit: a two-handed piece has a disc on both
        lim = float(opt(A, "--near")); n = len(todo)       # arms, and the left one can win (notes 103)
        far = [p for p in todo if p["fit"]["had"] and (p["fit"]["moved_mm"] > lim or p["fit"]["turn_deg"] > 10)]
        todo = [p for p in todo if p not in far]
        print("--near %g: %d fits that would move further left as they are:" % (lim, len(far)))
        for p in far: print("   %-60s %.1f mm %.0f deg" % (p["rel"].split("/")[-1][:60], p["fit"]["moved_mm"], p["fit"]["turn_deg"]))
        open(T + "/left_far.txt", "w", encoding="utf-8").write("".join("%s\t%.2f mm\t%.1f deg\n" % (p["rel"], p["fit"]["moved_mm"], p["fit"]["turn_deg"]) for p in far))
    if "--yes" not in A:
        try: os.startfile(os.path.normpath(T + "/report.txt"))
        except (AttributeError, OSError): pass
        if input("Write these %d fits and %d sockets into the library? [y/N] " % (len(todo), len(socks))).strip().lstrip(chr(0xfeff)).lower() not in ("y", "yes"):
            print("nothing written (the report stays in %s)" % T); return
    wrote, skipped, note = write(lib, T, todo, socks)
    print("wrote %d sidecars (backups in %s\\before); %s%s" % (len(wrote), T.replace("/", "\\"), note,
          "; skipped %d: %s" % (len(skipped), skipped[:3]) if skipped else ""))
    print("To undo: \"Seat connectors.bat\" restore")


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not A: print(__doc__)
    elif A[0] == "run": run(A[1], A[2:])
    elif A[0] == "search": search(A[1], A[2], A[3], int(A[4]), int(A[5]))
    elif A[0] == "restore": restore(opt(A, "--lib", LIB), A[1] if len(A) > 1 and not A[1].startswith("--") else None)
    elif A[0] == "write": write_task(opt(A, "--lib", LIB), A[1] if len(A) > 1 and not A[1].startswith("--") else None, A)
    else: print(__doc__)
