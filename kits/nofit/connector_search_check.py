"""Check kb.connect (the search from scratch, notes 098) against the library. Every fitted part of a type and maker
is searched once with all the type's connectors together (find_all: each place used by one connector); each
connector's result is then compared with the truth, the connector settled where the part's own fit / socket puts that
joint (as connector_at_joint.py). The search never sees the fits or sockets. Read-only on the library.

    BL  connector_search_check.py LIBRARY CAT MAKER OUT.json SPEC [SPEC ...] [--per N] [--only TEXT] [--shard i/n]
        SPEC = CONNECTOR.stl::SOURCE_REL::fit   or   CONNECTOR.stl::SOURCE_REL::socket:TYPE
  BL = blender --background --factory-startup --python connector_search_check.py --

Per part and connector: truth (median mm point to plane, share on the surface) and what the search said, and if
both have it, how far apart (place mm, tilt deg, turn deg). 'right' = within 0.5 mm and 5 deg of tilt.
"""
import sys, os, json, time, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]
from connector_try import sock


def run(lib, cat, maker, out, specs, A):
    from kb import connect as C, geo
    import carry_library as CL, masters as MS
    opt = lambda n: A[A.index(n) + 1] if n in A else None
    per = int(opt("--per") or 0); only = opt("--only"); shard = opt("--shard")
    cons, ref = [], {}
    for sp in specs:
        conn, src, mode = sp.split("::"); con = C.Connector.from_stl(conn, os.path.basename(conn)); cons.append(con)
        scs = json.load(open(lib + "/" + src + ".sockets.json", encoding="utf-8-sig")); typ = mode.split(":")[1] if mode.startswith("socket") else None
        ref[con.name] = (src, typ, MS.right_fit(scs)[0], sock(scs, typ) if typ else None)
        own = C.Surface(C.soup(lib + "/" + src + ".stl", scs.get("scale", 1.0)))
        print("%s: box %s, on its own part %.4f mm" % (con.name, con.box.round(2), float(np.median(own.dist(con.fine)[0]))), flush=True)
    srcs = {v[0] for v in ref.values()}
    P = [(rel, sc) for rel, sc in CL.scan(lib, [cat])[cat] if CL.maker(rel) == maker and rel not in srcs and (not only or only in rel) and MS.right_fit(sc)[0] is not None]
    if per: random.Random(5).shuffle(P); P = P[:per]
    if shard: i, n = map(int, shard.split("/")); P = P[i::n]
    rows = []
    for k, (rel, sc) in enumerate(P):
        t0 = time.time(); F0, left = MS.right_fit(sc)
        try: surf = C.Surface(C.soup(lib + "/" + rel + ".stl", sc.get("scale", 1.0)), mirror=left)
        except (OSError, ValueError): continue
        found = C.find_all(cons, surf); secs = time.time() - t0; line = []
        for con in cons:
            src, typ, Fsrc, Ssrc = ref[con.name]; f = found[con.name]
            if typ:
                S0 = sock(sc, typ); M0 = S0 @ np.linalg.inv(Ssrc) if S0 is not None else None
            else: M0 = np.linalg.inv(F0) @ Fsrc
            tr = C._result(*C.settle(con, surf, M0[:3, :3], M0[:3, 3])) if M0 is not None else None
            r = {"rel": rel, "kit": rel.split("/")[1], "left": left, "connector": con.name, "found": f["match"], "found_cover": f["cover"],
                 "found_same": f["same"], "found_level": f["level"], "wider": bool(f.get("wider")), "ambiguous": f.get("ambiguous"), "turned": f.get("turned"), "secs": round(secs, 1)}
            if tr is not None:
                Rt, Rf = tr["M"][:3, :3], f["M"][:3, :3]
                r.update(truth=tr["match"], truth_cover=tr["cover"], truth_same=tr["same"], truth_level=tr["level"],
                         place_mm=round(float(np.linalg.norm((Rf @ con.c + f["M"][:3, 3]) - (Rt @ con.c + tr["M"][:3, 3]))), 2),
                         tilt=round(float(np.degrees(np.arccos(np.clip(abs((Rf @ con.axis) @ (Rt @ con.axis)), -1, 1)))), 1), turn=round(geo.ang(Rf @ Rt.T), 1),
                         turn_lib=round(geo.ang(Rf @ M0[:3, :3].T), 1))   # against the library's joint as it is (a round connector's settle drifts in turn)
                r["verdict"] = ("right" if r["place_mm"] <= 0.5 and r["tilt"] <= 5 else "WRONG PLACE") if tr["same"] and f["same"] else \
                               "missed" if tr["same"] else "FALSE" if f["same"] else "no (right)"
                line.append("%s %.3f/%.2f->%.3f/%.2f %s%s" % (con.name[:8], tr["match"], tr["cover"], f["match"], f["cover"], r["verdict"],
                            " %.2fmm %.0f/%.0fdeg" % (r["place_mm"], r["tilt"], r["turn"]) if r["verdict"] in ("right", "WRONG PLACE") else ""))
            else:
                r["verdict"] = "FALSE?" if f["same"] else "no (no joint)"
                line.append("%s -> %.3f/%.2f %s" % (con.name[:8], f["match"], f["cover"], r["verdict"]))
            rows.append(r)
        print("%3d %-40s%s %4.0fs | %s" % (k + 1, os.path.basename(rel)[-40:], " L" if left else "  ", secs, " | ".join(line)), flush=True)
    json.dump(rows, open(out, "w", encoding="utf-8"), indent=0)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    k = 4
    while k < len(A) and not A[k].startswith("--"): k += 1
    run(A[0], A[1], A[2], A[3], A[4:k], A[k:])
