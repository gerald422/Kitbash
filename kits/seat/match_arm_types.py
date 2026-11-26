"""Stage 4 pads (Nov 26, notes 172): which arm type each written arm is, by Josh's shoulder cuts (setup only).

    BL kits/seat/match_arm_types.py -- OUT.json

The cuts are the auto pad-spot cuts in his Nov 23 seat file (`... pad spot cut (auto)`, each parented to its arm; the
shoulder surface the guide sees). Each is fitted onto every written arm by trimmed ICP of the cut's points only (the
mating surface, CLAUDE.md), from the file frame and from the arm's place on Torso 2. Left-only sculpts are tried as
their mirror image (as stage 3 showed them). An arm takes the type whose cut fits best: under 0.06 mm "same", under
0.15 mm "near"; arms matching no cut are the new types Josh seats and cuts once (one column per kit in the arm file).
Josh: "it should just be all arm types ... It shouldnt need to be every single arm"."""
import os, sys, json, glob, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
from mathutils.bvhtree import BVHTree
import geom as G, batch as B, make_torso_batch as MT, make_pad_batch as MP

SAME, NEAR = 0.06, 0.15
MX = np.diag([-1.0, 1, 1, 1])


def main(A):
    out = A[0]; lib = MT.LIB; t0 = time.time()
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser(MT.SRC["seat"]), load_ui=False); bpy.context.view_layer.update()
    ob = bpy.data.objects; S_sh = MT.sockets(MT.T2)
    cuts = []
    for c in ob:
        if not c.name.endswith("pad spot cut (auto)") or c.parent is None: continue
        arm = c.parent; rel = MP.rel_of(arm.name)
        if not rel or arm.get("kb_mirrored"): print("cut skipped (arm %s: %s)" % (arm.name, "mirrored left" if rel else "not in the library")); continue
        sc = B.sidecar(lib, rel)
        if "Shoulder R" not in (sc.get("exact") or []): print("cut skipped (%s: no written Shoulder R)" % rel); continue
        W = B.own_world(arm, rel, lib, sc); Wi = np.linalg.inv(W)
        P = G.verts_world(c) @ Wi[:3, :3].T + Wi[:3, 3]; P = P[np.linspace(0, len(P) - 1, min(len(P), 800)).astype(int)]
        cuts.append({"name": c.name.replace(" - pad spot cut (auto)", ""), "rel": rel, "maker": rel.split("/")[0], "P": P,
                     "A": S_sh["Shoulder R"] @ G.M4(sc["fits"]["Shoulder R"])})
    print("%d cuts: %s" % (len(cuts), ", ".join(c["name"] for c in cuts)), flush=True)
    makers_with_cuts = {c["maker"] for c in cuts}
    arms = []
    for p in sorted(glob.glob(os.path.join(lib, "*", "**", "*.sockets.json"), recursive=True)):
        rel = os.path.relpath(p, lib).replace("\\", "/")[:-13]
        if rel.startswith("_"): continue
        d = json.load(open(p, encoding="utf-8-sig"))
        if d.get("category") != "Arms" or d.get("noPad"): continue
        ex = set(d.get("exact") or [])
        if "Shoulder R" in ex: arms.append((rel, False, S_sh["Shoulder R"] @ G.M4(d["fits"]["Shoulder R"])))
        elif "Shoulder L" in ex: arms.append((rel, True, MX @ S_sh["Shoulder L"] @ G.M4(d["fits"]["Shoulder L"]) @ MX))
    print("%d arms to match" % len(arms), flush=True)
    res = []
    for n, (rel, left, A_x) in enumerate(arms):
        T = B.stl_tris(lib, rel, B.sidecar(lib, rel))
        if left: T = T[:, ::-1] * np.array([-1.0, 1, 1])
        V = T.reshape(-1, 3)
        bvh = BVHTree.FromPolygons([tuple(v) for v in V], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(T))])
        maker = rel.split("/")[0]
        mine = [c for c in cuts if c["maker"] == maker] if maker in makers_with_cuts else cuts
        best = (9.0, None)
        for c in mine:
            for M0 in (np.eye(4), np.linalg.inv(A_x) @ c["A"]):
                R, t, rms = G.icp(bvh, c["P"], M0[:3, :3], M0[:3, 3], iters=30, keep=0.8, lim=3.0)
                if rms < best[0]: best = (rms, c["name"])
            if best[0] < 0.02: break
        g = "same" if best[0] < SAME else "near" if best[0] < NEAR else "none"
        res.append({"rel": rel, "left": left, "type": best[1] if g != "none" else None, "best": best[1], "rms": round(best[0], 4), "grade": g})
        if n % 25 == 0: print("%d/%d %.0f s" % (n, len(arms), time.time() - t0), flush=True)
    json.dump({"cuts": [c["name"] for c in cuts], "arms": res}, open(out, "w", encoding="utf-8"), indent=1)
    import collections
    per = collections.Counter(r["type"] for r in res if r["type"]); none = [r for r in res if not r["type"]]
    print("\nper type:"); [print("  %3d %s" % (v, k)) for k, v in per.most_common()]
    kits = collections.Counter("/".join(r["rel"].split("/")[:2]) for r in none)
    print("\nno match: %d arms, by kit:" % len(none)); [print("  %3d %s" % (v, k)) for k, v in kits.most_common()]
    print("done %.0f s" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
