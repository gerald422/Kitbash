"""The shell (every pauldron's origin since notes 174) on each arm type by shape, not from Josh's per-arm setups
(Nov 28, Josh: "try to do a shape match or similar rather then working off of my setups").

    BL kits/seat/shell_on_arms.py -- ARM_TYPES.blend OUT.blend [--keep t5,..]
  BL = blender --background --factory-startup --python

Only reference: Arm 2B R's written Pad R (Josh's, stage 1). Pads sit on the TORSO the same whatever the arm (Nov 23:
his Intercessor pad 1.4 deg from his Assault one once both are on the torso), and every arm is written on the one
spacer (stage 3), so the shell starts where 2B R's sits on the torso. Then by shape: slid along its own +Z (out of the
crown) until it touches this arm's shoulder as it touches 2B R's: the 10th percentile of the shell's signed distances
to the arm (negative = inside the arm) matched to 2B R's. Shells listed in --keep (Josh moved them) are left."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import geom as G, batch as B, make_torso_batch as MT

Q, LIM = 10, 4.0


def tri_bvh(T): return BVHTree.FromPolygons([tuple(v) for v in T.reshape(-1, 3)], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(T))])


def own_tris(o):
    Ki = np.linalg.inv(G.M4(o["kb_own_in_obj"])); return G.tris(o) @ Ki[:3, :3].T + Ki[:3, 3]


def signed(bvh, P):
    d = np.empty(len(P))
    for k, p in enumerate(P):
        loc, n, _i, dist = bvh.find_nearest(Vector(p), 20.0)
        d[k] = 20.0 if loc is None else (dist if (Vector(p) - loc).dot(n) >= 0 else -dist)
    return d


def level(bvh, Vs, M, h):
    """Q-th percentile of the shell's signed distances to the arm, the shell at M (arm own) lifted h along its +Z"""
    L = M @ np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, h], [0, 0, 0, 1.0]])
    return float(np.percentile(signed(bvh, Vs @ L[:3, :3].T + L[:3, 3]), Q))


def main(A):
    src, out = A[0], A[1]; keep = set((B.opt(A, "--keep", "") or "").split(",")) - {""}
    if os.path.exists(out): raise SystemExit("%s exists: never overwritten" % out)
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}; lib = MT.LIB
    S_sh = MT.sockets(MT.T2); pad_2b = MT.sockets(MT.ARM)["Pad R"]
    P_t = S_sh["Shoulder R"] @ G.M4(B.sidecar(lib, MT.ARM)["fits"]["Shoulder R"]) @ pad_2b      # 2B R's Pad R, torso frame
    shells = sorted((i for i in by if i.endswith("_shell")), key=lambda i: int(i[1:-6]))
    Vs = own_tris(by[shells[0]]).reshape(-1, 3); Vs = Vs[np.linspace(0, len(Vs) - 1, 2500).astype(int)]   # the shell, crown frame
    ref = level(tri_bvh(B.stl_tris(lib, MT.ARM, B.sidecar(lib, MT.ARM))), Vs, pad_2b, 0.0)
    print("2B R: the shell's %dth percentile distance to the arm %.3f mm" % (Q, ref), flush=True)
    W = []
    for i in shells:
        t = i[:-6]; sh, arm, tor = by[i], by[t + "_arm"], by[t]
        if i in keep: W.append("%-6s %-48s kept (Josh moved it)" % (t, arm.name[:48])); continue
        M = np.linalg.inv(B.own(arm)) @ B.own(tor) @ P_t                    # torso-relative, in the arm's own frame
        bvh = tri_bvh(own_tris(arm))
        lo, hi = -LIM, LIM; f = lambda h: level(bvh, Vs, M, h) - ref
        flo, fhi = f(lo), f(hi); h = 0.0; note = ""
        if flo > 0: h, note = lo, "  (still clear at -%.0f mm: check)" % LIM
        elif fhi < 0: h, note = hi, "  (still in the arm at +%.0f mm: check)" % LIM
        else:
            for _ in range(22):
                mid = (lo + hi) / 2
                if f(mid) < 0: lo = mid
                else: hi = mid
            h = (lo + hi) / 2
        L = B.own(arm) @ M @ np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, h], [0, 0, 0, 1.0]])
        old = B.own(sh)
        sh.rotation_mode = 'QUATERNION'; sh.matrix_world = G.mat(L @ np.linalg.inv(G.M4(sh["kb_own_in_obj"]))); bpy.context.view_layer.update()
        sh["kb_seated"] = G.flat16(np.array(sh.matrix_world)); sh["kb_note"] = "shape: torso-relative from 2B R, lifted %.2f mm to touch as on 2B R" % h
        W.append("%-6s %-48s lift %+.2f mm; %.1f mm %.0f deg from the old start%s" % (t, arm.name[:48], h, np.linalg.norm(L[:3, 3] - old[:3, 3]), G.ang(L, old), note))
        print(W[-1], flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=out); print("SAVED", out, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except SystemExit as e: print("STOPPED:", e, flush=True)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
