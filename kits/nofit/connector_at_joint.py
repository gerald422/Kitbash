"""Check (Nov 14, notes 097): is a connector's shape on every part of a type where the library already puts that joint?
The connector starts where the part's own fit (or socket) says the joint is, settles by shape (ICP), and the script
reports how well it sits and how far it had to move. A part with the same connector design ends <= ~0.05 mm (it sits on
its own part at ~0.03-0.04 sampled) and moves only a little: then the library's joint and the connector agree.
Read-only on the library.

    BL  connector_at_joint.py LIBRARY CONNECTOR.stl SOURCE_REL CAT MAKER OUT.json fit|socket:TYPE
        fit          compare against the parts' fits (legs: their Waist fit)
        socket:Pad   compare against the parts' socket of this type (arms: Pad, Hand, Forearm)
  BL = blender --background --factory-startup --python connector_at_joint.py --
"""
import sys, os, json, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]
from connector_try import sock


def run(lib, conn, src, cat, maker, out, mode):
    from kb import carry, geo
    import carry_library as CL, masters as MS
    Cs = carry.sample(carry.soup(conn), 4000, 0); Cf = Cs[np.random.default_rng(1).choice(len(Cs), 800, replace=False)]; cc = Cs.mean(0)
    scs = json.load(open(lib + "/" + src + ".sockets.json", encoding="utf-8-sig")); Fsrc, _ = MS.right_fit(scs)
    typ = mode.split(":")[1] if mode.startswith("socket") else None; Ssrc = sock(scs, typ) if typ else None
    S = carry.Shape(lib + "/" + src + ".stl", scs.get("scale", 1.0))
    print("%s on its own part (sampled): %.3f mm" % (os.path.basename(conn), float(np.median(S.tree.query(Cf)[0]))), flush=True)
    rows = []
    for rel, sc in CL.scan(lib, [cat])[cat]:
        if CL.maker(rel) != maker or rel == src: continue
        F0, left = MS.right_fit(sc)
        if F0 is None: continue
        if typ:
            S0 = sock(sc, typ)
            if S0 is None: continue
            M0 = S0 @ np.linalg.inv(Ssrc)                    # reference coords -> this part's, so the sockets coincide
        else: M0 = np.linalg.inv(F0) @ Fsrc                  # ... so the fits coincide
        try: part = carry.Shape(lib + "/" + rel + ".stl", sc.get("scale", 1.0), 0, left)
        except (OSError, ValueError): continue
        d0 = float(np.median(part.tree.query(Cf @ M0[:3, :3].T + M0[:3, 3])[0]))
        R, t, d = geo.icp(Cf, part.tree, M0[:3, :3], M0[:3, 3], 60); M = carry.M4(R, t); D = M @ np.linalg.inv(M0)
        mm = float(np.linalg.norm(M[:3, :3] @ cc + M[:3, 3] - (M0[:3, :3] @ cc + M0[:3, 3])))
        r = {"rel": rel, "kit": rel.split("/")[1], "left": left, "start": round(d0, 3), "end": round(float(np.median(d)), 3),
             "q90": round(float(np.quantile(d, .9)), 3), "mm": round(mm, 2), "deg": round(geo.ang(D[:3, :3]), 1)}
        rows.append(r); print("%-52s%s start %.3f -> %.3f (q90 %.3f)  moved %.2f mm %.1f deg" % (os.path.basename(rel)[-52:], " L" if left else "  ", r["start"], r["end"], r["q90"], r["mm"], r["deg"]), flush=True)
    json.dump(rows, open(out, "w", encoding="utf-8"), indent=0)
    K = collections.defaultdict(list)
    for r in rows: K[r["kit"]].append(r)
    print("SUMMARY %s %s: %d parts" % (os.path.basename(conn), mode, len(rows)))
    for k, v in sorted(K.items()):
        good = [r for r in v if r["end"] <= 0.05]; near = [r for r in v if 0.05 < r["end"] <= 0.08]
        print("  %-24s n %3d | same shape (<=0.05): %3d, moved median %.2f mm %.1f deg | 0.05-0.08: %3d | other: %3d" % (
            k[:24], len(v), len(good), np.median([r["mm"] for r in good]) if good else 0, np.median([r["deg"] for r in good]) if good else 0,
            len(near), len(v) - len(good) - len(near)))


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    run(*A[:7])
