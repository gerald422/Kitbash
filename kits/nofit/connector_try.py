"""Trial (Nov 14, notes 096): Josh's hand-made connectors (a joint's mating surface cut from one reference part) matched
onto the other parts of the maker by shape, each part's fit then = the reference's fit moved by the match.
Checked against the fits the parts already have (their own fit is never used to find the match).

    BL  connector_try.py LIBRARY CONNECTOR.stl SOURCE_REL "CAT,CAT" MAKER OUT.json [--per 25] [--frame]
        --frame: no turning search, only sliding the connector over the part as it lies in its file (then ICP)
  BL = blender --background --factory-startup --python connector_try.py --

CONNECTOR.stl is in the source part's own file coordinates (as cut from it). Search: the connector at many places on
the part (24 square turns x 150 surface points), the best few refined by ICP (turning allowed). Left parts are
mirrored first and use the right-hand fit, as the library does.
"""
import sys, os, json, random, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]


FRAME = False
def run(lib, conn, src, cats, maker, out, per):
    from kb import carry, geo
    import carry_library as CL, masters as MS
    Cs = carry.sample(carry.soup(conn), 4000, 0); Cf = Cs[np.random.default_rng(1).choice(len(Cs), 600, replace=False)]; cc = Cs.mean(0)
    w, v = np.linalg.eigh(np.cov((Cs - cc).T)); nrm = v[:, 0]                       # the connector's flattest direction
    scs = json.load(open(lib + "/" + src + ".sockets.json", encoding="utf-8-sig")); Fsrc, _ = MS.right_fit(scs)
    S = carry.Shape(lib + "/" + src + ".stl", scs.get("scale", 1.0)); d0 = float(np.median(S.tree.query(Cs)[0]))
    print("connector %s: %d triangles, box %s; on its own part as cut: median %.3f mm" % (os.path.basename(conn), len(carry.soup(conn)), np.ptp(Cs, 0).round(2), d0), flush=True)
    P = [(r, s) for c in cats for r, s in CL.scan(lib, [c])[c] if CL.maker(r) == maker and MS.right_fit(s)[0] is not None and r != src]
    random.Random(5).shuffle(P); P = P[:per]; rows = []
    def med(tree, X): return float(np.median(tree.query(X)[0]))
    for k, (rel, sc) in enumerate(P):
        t0 = time.time(); F0, left = MS.right_fit(sc)
        try: part = carry.Shape(lib + "/" + rel + ".stl", sc.get("scale", 1.0), 0, left)
        except (OSError, ValueError): continue
        tree = part.tree; pts = part.S[np.random.default_rng(2).choice(len(part.S), 150, replace=False)]; sub = Cf[:120]
        cand = [(med(tree, sub), np.eye(3), np.zeros(3))]                          # as it lies: the kit's own frame
        for R in ([np.eye(3)] if FRAME else carry.ROTS):            # --frame: keep the turn the part has in its file
            Rc = sub @ R.T; c0 = cc @ R.T
            for p in pts:
                t = p - c0; cand.append((med(tree, Rc + t), R, t))
        cand.sort(key=lambda c: c[0]); best = None
        for _, R, t in cand[:6]:
            R2, t2, d = geo.icp(Cf, tree, R, t, 40); m = float(np.median(d))
            if best is None or m < best[0]: best = (m, R2, t2)
        m, R, t = best; M = carry.M4(R, t); F = Fsrc @ np.linalg.inv(M)
        # does the connector fix the part's turn about its own axis? turned 30 deg in place, how far off is it then
        ax = R @ nrm; c1 = R @ cc + t; th = np.radians(30); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); Rt = np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
        spun = med(tree, ((Cf @ R.T + t) - c1) @ Rt.T + c1)
        r = {"rel": rel, "left": left, "match": round(m, 3), "spun30": round(spun, 3), "mm": round(float(np.linalg.norm(carry.point("fit", F) - carry.point("fit", F0))), 3),
             "deg": round(carry.ang(F, F0), 2), "secs": round(time.time() - t0, 1)}
        rows.append(r); print("%2d %-50s match %.3f (turned 30: %.3f)  vs its fit: %.2f mm %.1f deg" % (k + 1, os.path.basename(rel)[-50:], m, spun, r["mm"], r["deg"]), flush=True)
    json.dump({"connector": conn, "source": src, "on_source": d0, "rows": rows}, open(out, "w", encoding="utf-8"), indent=0)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    per = int(A[A.index("--per") + 1]) if "--per" in A else 25
    FRAME = "--frame" in A
    run(A[0], A[1], A[2], A[3].split(","), A[4], A[5], per)
