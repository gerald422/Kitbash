"""Carry Josh's seat of one pauldron to the rest of its kit by the inner surface (Nov 26, stage 4 pauldrons).

    BL kits/seat/carry_by_shape.py -- SRC.blend OUT.blend FROM_ID@KIT[,FROM_ID@KIT...] [--only ID,ID]

Several FROM_IDs may share a KIT (Josh seats one per inner shape): each other pauldron takes the best of them.
  BL = blender --background --factory-startup --python

Josh: "they by type all have the same internal shape. there is a certain curve that is shared across each type ...
find that inner surface and then copy the previous placement" (details are sculpted on top). So:
- the inner surface of every pauldron: the triangles on the hollow side, i.e. facing the centre of the dome (a sphere
  fitted to them, refined) and seeing that centre with nothing of the pauldron in the way (so the undersides of
  sculpted detail on the outside are left out);
- his pauldron's inner surface, as he placed it in the shell, is fitted onto each other pauldron's inner surface only
  (trimmed ICP from 322 starts over every turn), and scored both ways (theirs back onto his): the curve sets depth and
  tilt, the edge of the inner surface sets the spin. Its place in the shell follows.
Matches over SURE (0.05 mm; the same sculpt underneath should be near 0.01), or with a second spin nearly as good,
are flagged; over GOOD (0.15 mm) the pauldron is left where it started. Earlier tries on the same pack failed: adding
his move (`batch.py apply --delta`), his contact patch against the whole pauldron, and the top."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import geom as G, batch as B

GOOD, SURE, TIE_MM, TIE_DEG = 0.15, 0.05, 0.01, 10.0


def tri_bvh(T): return BVHTree.FromPolygons([tuple(v) for v in T.reshape(-1, 3)], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(T))])
def sub(P, n): return P[np.linspace(0, len(P) - 1, min(len(P), n)).astype(int)]


def inner(o):
    """the pauldron's inner surface in its own coordinates: (points, BVH of those triangles, share of the area)"""
    Ki = np.linalg.inv(G.M4(o["kb_own_in_obj"])); T = G.tris(o) @ Ki[:3, :3].T + Ki[:3, 3]
    C = T.mean(1); N = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); A = np.linalg.norm(N, axis=1); N = N / np.maximum(A, 1e-12)[:, None]
    c, _r = G.sphere_fit(C); m = np.ones(len(C), bool)
    for _ in range(8):                               # faces looking at the dome's centre, refitted on those
        d = c - C; m2 = (N * d).sum(1) / np.maximum(np.linalg.norm(d, axis=1), 1e-9) > 0.5
        if m2.sum() < 50: break
        m = m2; c, _r = G.sphere_fit(C[m])
    full = tri_bvh(T); keep = []
    for k in np.nonzero(m)[0]:                       # ... and seeing it: nothing of the pauldron in between
        d = c - C[k]; L = np.linalg.norm(d)
        if full.ray_cast(Vector(C[k] + N[k] * 0.02), Vector(d / L), L)[0] is None: keep.append(k)
    Ti = T[np.array(keep, int)]
    return np.concatenate([Ti.mean(1), Ti.reshape(-1, 3)]), tri_bvh(Ti), float(A[keep].sum() / A.sum())


def main(A):
    src, out, froms = A[0], A[1], A[2].split(",")
    only = set((B.opt(A, "--only", "") or "").split(",")) - {""}
    if os.path.exists(out): raise SystemExit("%s exists: never overwritten" % out)
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    frame = lambda o: B.own(by[o["kb_parent"]]) @ G.M4(o["kb_on_frame"])      # the frame it sits on in the shell (world)
    starts = [G.rot_to(np.array([0, 0, 1.0]), dv) @ G.rot((0, 0, 1), s) for dv in G.fib(40) for s in range(0, 360, 45)]
    W, flagged = [], []
    kits = {}                                        # kit -> his pauldrons there (several per pack: each other one takes
    for fk in froms:                                 # the one whose inner surface it matches best)
        fid, _, kit = fk.partition("@"); kits.setdefault(kit, []).append(fid)
    his = {f for fs in kits.values() for f in fs}
    for kit, fids in kits.items():
        refs = []
        for fid in fids:
            j = by[fid]; Xj = np.linalg.inv(frame(j)) @ B.own(j)               # his pauldron: own -> shell frame
            Pj, bj, sh = inner(j); Ps = Pj @ Xj[:3, :3].T + Xj[:3, 3]          # its inner surface, as he placed it
            refs.append((fid, j.name, Xj, bj, Ps))
            W.append("%s@%s (%s): inner surface %.0f%% of its area" % (fid, kit, j.name, 100 * sh)); print(W[-1], flush=True)
        suf = fids[0].split("_", 1)[1]
        for i, o in sorted(by.items(), key=lambda kv: int(kv[0].split("_")[0][1:]) if kv[0].split("_")[0][1:].isdigit() else 0):
            if i in his or "_" not in i or i.split("_", 1)[1] != suf or o["kb_role"] != "part": continue
            if only and i not in only: continue
            if kit and not any(cl.name.startswith(kit) for cl in o.users_collection): continue
            Po, bo, sho = inner(o); Pt = sub(Po, 1500)
            Xo = np.linalg.inv(frame(o)) @ B.own(o)
            fits = []
            for fid, jname, Xj, bj, Ps in refs:
                Pc, Pf = sub(Ps, 250), sub(Ps, 1500)
                cand = [(np.linalg.inv(X)[:3, :3], np.linalg.inv(X)[:3, 3]) for X in (Xj, Xo)] + [(R0, Po.mean(0) - R0 @ Ps.mean(0)) for R0 in starts]
                coarse = sorted((G.icp(bo, Pc, R0, t0, iters=8, keep=0.85, lim=10.0) for R0, t0 in cand), key=lambda f: f[2])
                seen = []
                for R, t, _r in coarse:              # M: his shell frame -> their own
                    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t
                    if any(G.ang(M, S) < 5 and np.linalg.norm(M[:3, 3] - S[:3, 3]) < 1 for S in seen): continue
                    seen.append(M)
                    if len(seen) > 6: break
                    R, t, r1 = G.icp(bo, Pf, R, t, iters=40, keep=0.85, lim=3.0)
                    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t
                    back = np.linalg.inv(Xj) @ np.linalg.inv(M)                # their own -> his own: theirs onto his
                    Q = Pt @ back[:3, :3].T + back[:3, 3]
                    d = np.array([(bj.find_nearest(Vector(q), 3.0)[3] or 9.0) for q in Q])
                    r2 = float(np.sqrt(np.mean(np.sort(d)[: int(len(d) * 0.85)] ** 2)))
                    fits.append((max(r1, r2), np.linalg.inv(M), r1, r2, fid, jname))
                if fits and min(f[0] for f in fits) < 0.03: break             # a sure match: no need to try his others
            fits.sort(key=lambda f: f[0]); best = fits[0]
            rival = next((f for f in fits[1:] if f[4] == best[4] and f[0] - best[0] < TIE_MM and G.ang(f[1], best[1]) > TIE_DEG), None)
            rms = best[0]; X = best[1] if rms <= GOOD else Xo
            o.rotation_mode = 'QUATERNION'
            o.matrix_world = G.mat(frame(o) @ X @ np.linalg.inv(G.M4(o["kb_own_in_obj"])))
            if rms <= GOOD: o["kb_applied"] = "inner surface fit to %s (%s), %.3f mm" % (best[4], os.path.basename(src), rms)
            flag = []
            if rms > GOOD: flag.append("no match: left where it was")
            elif rms > SURE: flag.append("loose")
            if rival and rms <= GOOD: flag.append("another spin fits nearly as well (%.3f mm, %.0f deg away)" % (rival[0], G.ang(rival[1], X)))
            if flag: flagged.append(i)
            W.append("  %-9s %-46s inner %3.0f%%  %.3f mm on %-8s (his on theirs %.3f, theirs on his %.3f)  %s"
                     % (i, o.name[:46], 100 * sho, rms, best[4], best[2], best[3], "; ".join(flag) or "ok"))
            print(W[-1], flush=True)
    bpy.context.view_layer.update()
    print("flagged: %s" % (" ".join(flagged) or "none"), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=out); print("SAVED", out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except SystemExit as e: print("STOPPED:", e, flush=True)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
