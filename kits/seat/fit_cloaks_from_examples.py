"""Cloaks on Torso 2 from Josh's examples (notes 135): shape only, the contact patch, never the cloak geometry.

    BL kits/seat/fit_cloaks_from_examples.py -- BATCH.blend prove|all OUT.json   (writes poses to OUT; changes nothing)
  BL = blender --background --factory-startup --python

Josh placed one cloak of each style in the cloaks batch (make_cloak_batch.py): CyberBrush Bug Hunters Cloak 1, with
circles on the straps (c1), and Marta 49 March 2026 Cloak 2, without (c8).
- A style's contact patch is the marine surface within 0.3 mm of his placed cloak: Torso 2, the pack, the arm, the
  pad, the head, the legs, the spacer and the guide.
- A cloak is fitted by ICP of that patch onto its surface. It is scored by trimmed rms plus how much of the cloak ends
  inside the torso.
- Same series: start from the example, moved by the bounding-box centres, then a local refine only.
- Other cloaks: 24 axis turns x both styles. That is unreliable: the proof run found neither example that way. Look at
  every result before using it.

prove: a local refine from Josh's own two placements (it should keep them). all: every other cloak.
OUT: {id: {name, style, searched, rms, inside, E (cloak own -> Torso 2 own, row-major), off_from_current}}."""
import os, sys, json, time, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
from mathutils.bvhtree import BVHTree
import geom as G, batch as B

LIB = "D:/Kitbash Library"
EX = {"circles": "c1", "plain": "c8"}                          # Josh's examples (column ids)
SERIES = {"CyberBrush Bug Hunters": "c1", "Marta 49 March 2026": "c8"}
PATCH_MM, PATCH_N = 0.3, 700


def main(A):
    blend, mode, out = A[0], A[1], A[2]
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser(blend), load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    lib_tris = lambda o: B.stl_tris(LIB, o["kb_rel"], B.sidecar(LIB, o["kb_rel"])).reshape(-1, 3)
    in_host = lambda o, host: np.linalg.inv(B.own(by[host])) @ B.own(o)
    bvh = lambda V: BVHTree.FromPolygons([tuple(v) for v in V], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(V) // 3)])

    MV = []                                              # the marine of column c1 in Torso 2 own coordinates (all columns alike)
    for part in ("", "_pack", "_arm", "_pad", "_head", "_legs", "_spacer", "_guide"):
        o = by.get("c1" + part)
        if o is None: continue
        if o["kb_rel"].startswith("connector"):
            M = np.linalg.inv(B.own(by["c1"])); MV.append(G.verts_world(o) @ M[:3, :3].T + M[:3, 3]); continue
        T = lib_tris(o); M = in_host(o, "c1"); MV.append(T @ M[:3, :3].T + M[:3, 3])
    allv = np.unique(np.vstack(MV).round(3), axis=0); torso_b = bvh(MV[0])
    patch = {}
    for st, c in EX.items():
        T = lib_tris(by[c + "_cloak"]); M = in_host(by[c + "_cloak"], c); bc = bvh(T @ M[:3, :3].T + M[:3, 3])
        d = np.array([bc.find_nearest(v)[3] for v in allv]); P = allv[d < PATCH_MM]
        patch[st] = P[np.random.default_rng(1).choice(len(P), min(PATCH_N, len(P)), replace=False)]
        print("patch", st, len(P), "points; centre", np.round(P.mean(0), 1), flush=True)

    R24 = []
    for perm in itertools.permutations(range(3)):
        for sg in itertools.product((1, -1), repeat=3):
            R = np.zeros((3, 3))
            for i, (p, s) in enumerate(zip(perm, sg)): R[i, p] = s
            if np.linalg.det(R) > 0: R24.append(R)

    def score(bcl, Vown, R, t, P):
        """P (Torso 2) into cloak own by (R, t): trimmed rms onto the cloak, and the share of the cloak inside the torso"""
        d = np.sort([bcl.find_nearest(q)[3] for q in P @ R.T + t]); rms = float(np.sqrt((d[:int(.8 * len(d))] ** 2).mean()))
        W = Vown[::max(1, len(Vown) // 1500)] @ R + (-R.T @ t); inside = 0
        for w in W:
            loc, n, _, dd = torso_b.find_nearest(w)
            if loc is not None and dd < 3 and np.dot(np.array(w) - np.array(loc), np.array(n)) < -0.05: inside += 1
        return rms, inside / len(W)

    def local(o, st, E0):
        T = lib_tris(o); bcl = bvh(T); Vown = np.unique(T.round(3), axis=0); P = patch[st]
        Ei = np.linalg.inv(E0); R, t = Ei[:3, :3], Ei[:3, 3]
        for lim in (3.0, 1.5, 0.8): R, t, rms = G.icp(bcl, P, R, t, iters=20, keep=0.8, lim=lim)
        r, ins = score(bcl, Vown, R, t, P); return r + 4 * ins, st, R, t, r, ins

    def search(o):
        T = lib_tris(o); bcl = bvh(T); Vown = np.unique(T.round(3), axis=0); ctr = (T.min(0) + T.max(0)) / 2; best = None
        for st, P in patch.items():
            for R in R24:
                Rr, t = R, ctr - R @ P.mean(0)
                for lim in (8.0, 4.0, 1.5): Rr, t, rms = G.icp(bcl, P, Rr, t, iters=15, keep=0.8, lim=lim)
                if rms >= 9: continue
                r, ins = score(bcl, Vown, Rr, t, P)
                if best is None or r + 4 * ins < best[0]: best = (r + 4 * ins, st + "?", Rr, t, r, ins)
        return best

    def series_start(o):
        for pre, c in SERIES.items():
            if o.name.startswith(pre):
                ex = by[c + "_cloak"]; Te, To = lib_tris(ex), lib_tris(o)
                sh = np.eye(4); sh[:3, 3] = (Te.min(0) + Te.max(0)) / 2 - (To.min(0) + To.max(0)) / 2
                return ("circles" if c == "c1" else "plain"), in_host(ex, c) @ sh
        return None, None

    ex_ids = [c + "_cloak" for c in EX.values()]
    todo = ex_ids if mode == "prove" else [i for i in by if i.endswith("_cloak") and i not in ex_ids]
    res = {}
    for i in todo:
        t0 = time.time(); o = by[i]; host = i.split("_")[0]
        if mode == "prove": best = local(o, "circles" if i == ex_ids[0] else "plain", in_host(o, host))
        else:
            st, E0 = series_start(o); best = local(o, st, E0) if st else search(o)
        s, st, R, t, r, ins = best
        E = np.eye(4); E[:3, :3] = R.T; E[:3, 3] = -R.T @ t              # cloak own -> Torso 2 own
        off = G.off(E, in_host(o, host))
        res[i] = dict(name=o.name, style=st.rstrip("?"), searched=st.endswith("?"), rms=r, inside=ins, E=G.flat16(E), off_from_current=off)
        print("%-10s %-36s %-8s rms %.3f inside %.3f  vs current %.2f mm %.1f deg  (%.0fs)" % (i, o.name[:36], st, r, ins, off[0], off[1], time.time() - t0), flush=True)
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
