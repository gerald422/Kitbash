"""Trial (Nov 14, notes 096 / 097): Josh's hand-made connectors (a joint's mating surface cut from one reference part)
matched onto the other parts of the maker by shape, searching from scratch (each part's own fit / sockets are never used
to find the match, only to check it). Read-only on the library.

    BL  connector_try.py LIBRARY CONNECTOR.stl SOURCE_REL "CAT,CAT" MAKER OUT.json [options]
        --per 25         parts to try
        --frame          no turning search, only sliding the connector over the part as it lies in its file (then ICP)
        --top 6 --pts 150   candidates refined by ICP / surface points tried (wider = slower, finds more)
        --fit            compare the part's fit (the reference's fit moved by the match) with its library fit
        --sockets "Pad,Hand"   compare a socket the reference has (moved by the match) with the part's own
        --padfit         CATS are pads, the reference is an arm: compare the pad's fit onto the arm's Pad socket
        --need Forearm   only parts that have this socket
  BL = blender --background --factory-startup --python connector_try.py --

CONNECTOR.stl is in the source part's own file coordinates (as cut from it; `connector_export.py` writes it from Josh's
.blend). Left parts are mirrored first and use the right-hand fit / sockets, as the library does.
Nov 14 (097): this search from scratch is too weak for production (wrist B found on 7 of 25 arms that all have it, the
pad spot on 0 of 25); `connector_at_joint.py` shows the shapes are there.
"""
import sys, os, json, random, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]
MX = np.diag([-1.0, 1, 1, 1])


def sock(sc, typ):
    """the part's socket of this type as on a right part (4x4), or None"""
    for s in sc.get("sockets", []):
        if s["type"] == typ + " R": return np.array(s["matrix"]).reshape(4, 4)
    for s in sc.get("sockets", []):
        if s["type"] == typ + " L": return MX @ np.array(s["matrix"]).reshape(4, 4) @ MX
    return None


def run(lib, conn, src, cats, maker, out, A):
    from kb import carry, geo
    import carry_library as CL, masters as MS
    def opt(n, d=None): return A[A.index(n) + 1] if n in A else d
    per = int(opt("--per", 25)); frame = "--frame" in A; top = int(opt("--top", 6)); npts = int(opt("--pts", 150))
    socks = [s for s in (opt("--sockets", "") or "").split(",") if s]; need = opt("--need")
    Cs = carry.sample(carry.soup(conn), 4000, 0); Cf = Cs[np.random.default_rng(1).choice(len(Cs), 600, replace=False)]; cc = Cs.mean(0)
    w, v = np.linalg.eigh(np.cov((Cs - cc).T)); nrm = v[:, 0]                       # the connector's flattest direction
    scs = json.load(open(lib + "/" + src + ".sockets.json", encoding="utf-8-sig")); Fsrc, _ = MS.right_fit(scs)
    Ssrc = {t: sock(scs, t) for t in socks}
    S = carry.Shape(lib + "/" + src + ".stl", scs.get("scale", 1.0)); d0 = float(np.median(S.tree.query(Cs)[0]))
    print("connector %s: box %s; on its own part as cut: median %.3f mm" % (os.path.basename(conn), np.ptp(Cs, 0).round(2), d0), flush=True)
    P = [(r, s) for c in cats for r, s in CL.scan(lib, [c])[c] if CL.maker(r) == maker and MS.right_fit(s)[0] is not None and r != src
         and (need is None or sock(s, need) is not None)]
    random.Random(5).shuffle(P); P = P[:per]; rows = []
    def med(tree, X): return float(np.median(tree.query(X)[0]))
    for k, (rel, sc) in enumerate(P):
        t0 = time.time(); F0, left = MS.right_fit(sc)
        try: part = carry.Shape(lib + "/" + rel + ".stl", sc.get("scale", 1.0), 0, left)
        except (OSError, ValueError): continue
        tree = part.tree; pts = part.S[np.random.default_rng(2).choice(len(part.S), npts, replace=False)]; sub = Cf[:120]
        cand = [(med(tree, sub), np.eye(3), np.zeros(3))]                          # as it lies: the kit's own frame
        for R in ([np.eye(3)] if frame else carry.ROTS):            # --frame: keep the turn the part has in its file
            Rc = sub @ R.T; c0 = cc @ R.T
            for p in pts:
                t = p - c0; cand.append((med(tree, Rc + t), R, t))
        cand.sort(key=lambda c: c[0]); best = None
        for _, R, t in cand[:top]:
            R2, t2, d = geo.icp(Cf, tree, R, t, 40); m = float(np.median(d))
            if best is None or m < best[0]: best = (m, R2, t2, float(np.quantile(d, 0.9)))
        m, R, t, q90 = best; M = carry.M4(R, t)
        # does the connector fix the part's turn about its own axis? turned 30 deg in place, how far off is it then
        ax = R @ nrm; c1 = R @ cc + t; th = np.radians(30); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); Rt = np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
        spun = med(tree, ((Cf @ R.T + t) - c1) @ Rt.T + c1)
        r = {"rel": rel, "left": left, "match": round(m, 3), "q90": round(q90, 3), "spun30": round(spun, 3)}; txt = ""
        if "--fit" in A or not (socks or "--padfit" in A):
            F = Fsrc @ np.linalg.inv(M); r["mm"] = round(float(np.linalg.norm(carry.point("fit", F) - carry.point("fit", F0))), 3); r["deg"] = round(carry.ang(F, F0), 2)
            txt += "  fit %.2f mm %.1f deg" % (r["mm"], r["deg"])
        for typ in socks:
            S0 = sock(sc, typ)
            if S0 is None or Ssrc[typ] is None: continue
            S1 = M @ Ssrc[typ]; r[typ + "_mm"] = round(float(np.linalg.norm(S1[:3, 3] - S0[:3, 3])), 3); r[typ + "_deg"] = round(carry.ang(S1, S0), 2)
            txt += "  %s socket %.2f mm %.1f deg" % (typ, r[typ + "_mm"], r[typ + "_deg"])
        if "--padfit" in A:
            F = np.linalg.inv(sock(scs, "Pad")) @ np.linalg.inv(M)     # pad -> reference arm -> its Pad socket's frame
            r["mm"] = round(float(np.linalg.norm(carry.point("fit", F) - carry.point("fit", F0))), 3); r["deg"] = round(carry.ang(F, F0), 2)
            X = np.c_[part.full, np.ones(len(part.full))]; r["surf_mm"] = round(float(np.median(np.linalg.norm((X @ F.T - X @ F0.T)[:, :3], axis=1))), 3)
            txt += "  pad fit %.2f mm %.1f deg; surface moved %.2f mm" % (r["mm"], r["deg"], r["surf_mm"])
        r["secs"] = round(time.time() - t0, 1); rows.append(r)
        print("%2d %-46s%s match %.3f q90 %.3f (turned 30: %.3f)%s" % (k + 1, os.path.basename(rel)[-46:], " L" if left else "  ", m, q90, spun, txt), flush=True)
    json.dump({"connector": conn, "source": src, "on_source": d0, "frame": frame, "rows": rows}, open(out, "w", encoding="utf-8"), indent=0)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    run(A[0], A[1], A[2], A[3].split(","), A[4], A[5], A[6:])
