"""Check (Nov 14, notes 097): does the arm's pad spot pin a pauldron down by itself? Each pad starts at its library
fit on the reference arm, is knocked off (15 deg about the spot, 1.5 mm), and the pad spot pulls it back by shape (ICP).
Reports where it ends: moved (median over the pad's surface), turn about the spot's own axis, and tilt. Read-only.
Nov 14: from its fit it stays (0.2 mm); knocked off, it comes back within 0.5 mm less than half the time: the dome sets
the pad's seat and depth, not its place on the dome (that has to come from the pad master / the pad's inside).

    BL  pad_pullback.py LIBRARY PADSPOT.stl ARM_REL MAKER OUT.json [--per 25]
  BL = blender --background --factory-startup --python pad_pullback.py --
"""
import sys, os, json, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path[:0] = [REPO, HERE]


def rot(ax, deg):
    ax = ax / np.linalg.norm(ax); th = np.radians(deg); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def run(lib, conn, src, maker, out, per):
    from kb import carry, geo
    import carry_library as CL, masters as MS
    Cs = carry.sample(carry.soup(conn), 4000, 0); Cf = Cs[np.random.default_rng(1).choice(len(Cs), 800, replace=False)]; cc = Cs.mean(0)
    nrm = np.linalg.eigh(np.cov((Cs - cc).T))[1][:, 0]
    def twist(Rd):
        """turn of Rd about the spot's own axis, and the rest (tilt), degrees"""
        w = np.sqrt(max(0, 1 + np.trace(Rd))) / 2
        v = np.array([Rd[2, 1] - Rd[1, 2], Rd[0, 2] - Rd[2, 0], Rd[1, 0] - Rd[0, 1]]) / (4 * w) if w > 1e-6 else np.zeros(3)
        tw = 2 * np.degrees(np.arctan2(v @ nrm, w)); return float(tw), geo.ang(Rd @ rot(nrm, tw).T)
    scs = json.load(open(lib + "/" + src + ".sockets.json", encoding="utf-8-sig"))
    S = next(np.array(s["matrix"]).reshape(4, 4) for s in scs["sockets"] if s["type"] == "Pad R")
    P = [(r, s) for r, s in CL.scan(lib, ["Shoulder Pads"])["Shoulder Pads"] if CL.maker(r) == maker and MS.right_fit(s)[0] is not None]
    random.Random(5).shuffle(P); P = P[:per]; rows = []; rng = np.random.default_rng(7)
    for k, (rel, sc) in enumerate(P):
        F0, left = MS.right_fit(sc)
        try: part = carry.Shape(lib + "/" + rel + ".stl", sc.get("scale", 1.0), 0, left)
        except (OSError, ValueError): continue
        A0 = S @ F0; M0 = np.linalg.inv(A0)                    # arm coords -> pad coords at the library fit
        d_lib = np.asarray(part.tree.query(Cf @ M0[:3, :3].T + M0[:3, 3])[0]); ends = []
        X = (np.c_[part.full, np.ones(len(part.full))] @ A0.T)[:, :3]
        for trial in range(6):
            K = np.eye(4)
            if trial: K[:3, :3] = rot(rng.normal(size=3), 15.0); K[:3, 3] = cc - K[:3, :3] @ cc + rng.normal(size=3) / np.sqrt(3) * 1.5
            Ms = M0 @ K; R, t, d = geo.icp(Cf, part.tree, Ms[:3, :3], Ms[:3, 3], 60)
            D = np.linalg.inv(carry.M4(R, t)) @ np.linalg.inv(A0)
            moved = float(np.median(np.linalg.norm((np.c_[X, np.ones(len(X))] @ D.T)[:, :3] - X, axis=1))); tw, tilt = twist(D[:3, :3])
            ends.append((float(np.median(d)), moved, tw, tilt))
        e = np.array(ends)
        r = {"rel": rel, "left": left, "at_fit": round(float(np.median(d_lib)), 3), "from_fit": [round(x, 3) for x in ends[0]],
             "knocked_match": e[1:, 0].round(3).tolist(), "knocked_moved": e[1:, 1].round(2).tolist(), "knocked_turn": e[1:, 2].round(1).tolist(), "knocked_tilt": e[1:, 3].round(1).tolist()}
        rows.append(r)
        print("%2d %-40s%s at its fit %.3f | from fit: moved %.2f mm | knocked x5: moved %s turn %s tilt %s" % (
            k + 1, os.path.basename(rel)[-40:], " L" if left else "  ", r["at_fit"], ends[0][1], r["knocked_moved"], e[1:, 2].round(0).tolist(), r["knocked_tilt"]), flush=True)
    json.dump(rows, open(out, "w", encoding="utf-8"), indent=0)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    run(*A[:5], int(A[A.index("--per") + 1]) if "--per" in A else 25)
