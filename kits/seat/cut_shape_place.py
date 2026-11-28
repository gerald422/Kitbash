"""Place the shell on arms by the SHAPE of Josh's hand cuts (Nov 28, Josh: "the shape is what matters. not the cut. not
the geometry ... match this SHAPE across all of the marfil assault arms").

    BL kits/seat/cut_shape_place.py -- CUTS.blend OUT_DIR N SEED [--kit AssaultMarines-V2]
  BL = blender --background --factory-startup --python

CUTS.blend: Josh's cuts on the raw Assault Arm 1 R-A (`76-Arm-1-R-A.002` and `..._AppliedMods`), in the maker's file
coordinates (the library's Arm 1A R is that file moved: origin.from_file).
1. Each cut is resampled evenly over its surface (by area), so its own vertices / triangles never count: only its form.
2. One way only: every cut point's distance to the arm's surface (the rest of the arm, and where the cut ends, don't
   count). From 48 turns covering every direction about the cut's centre (posed arms turn the shoulder), robust
   point-to-surface fitting (10% of points may miss), the two cuts fitted as one rigid pair; each cut alone too: they
   must agree.
3. A match: 90% of the cut within 0.05 mm of the arm, the two cuts within 0.5 mm / 2 deg of each other.
4. The shell goes across through the cut: its fit onto Arm 2B R (Josh's written Pad R) and onto the arm.
Renders N random Assault arms (not 2B R) with N random pauldrons (from the library, origin on Pad R)."""
import os, sys, json, glob, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
from mathutils import Vector
import geom as G, batch as B, make_torso_batch as MT
from shell_to_group import tri_bvh, dense
from kb import origin as OG

SRC = "Mar Fil - Tacticus/AssaultMarines-V2/Arms/MarFil Assault - Arm 1A R"
NP, TOL, LAND, AGREE_MM, AGREE_DEG = 3000, 0.05, 0.90, 0.5, 2.0
STARTS = None


def fit(P, bvh, M0):
    """P onto the surface in bvh: 48 turns about P's centre, placed where M0 puts it; (share within TOL, M)"""
    global STARTS
    if STARTS is None: STARTS = [G.rot_to(np.array([0, 0, 1.0]), d) @ G.rot((0, 0, 1), a) for d in G.fib(16) for a in (0, 120, 240)]
    c = P.mean(0); c1 = M0[:3, :3] @ c + M0[:3, 3]; Pc = P[::max(1, len(P) // 200)]
    co = []
    for R0 in STARTS:
        R = R0 @ M0[:3, :3]; co.append(G.icp(bvh, Pc, R, c1 - R @ c, iters=12, keep=0.9, lim=8.0))
    best = None
    for R, t, _r in sorted(co, key=lambda f: f[2])[:4]:
        R, t, rms = G.icp(bvh, P, R, t, iters=40, keep=0.9, lim=2.0)
        Q = P @ R.T + t; d = np.array([G.near_d(bvh, q, 1.0, 1.0) for q in Q])
        sh = float((d < TOL).mean())
        if best is None or sh > best[0]: M = np.eye(4); M[:3, :3], M[:3, 3] = R, t; best = (sh, M, rms)
    return best


def main(A):
    blend, outdir, N, seed = A[0], A[1], int(A[2]), int(A[3]); kit = B.opt(A, "--kit", "AssaultMarines-V2")
    lib = MT.LIB; rng = np.random.default_rng(7); rnd = random.Random(seed)
    bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False); bpy.context.view_layer.update()
    ob = bpy.data.objects
    F = np.array(OG.from_file(B.sidecar(lib, SRC)) or np.eye(4).ravel(), float).reshape(4, 4)      # maker file -> Arm 1A R now
    cuts = []
    src_bvh = tri_bvh(B.stl_tris(lib, SRC, B.sidecar(lib, SRC)))
    for nm in ("76-Arm-1-R-A.002", "76-Arm-1-R-A_AppliedMods"):
        T = G.tris(ob[nm]); M = F @ np.array(ob[nm].matrix_world); T = T @ M[:3, :3].T + M[:3, 3]
        on = np.array([max(G.near_d(src_bvh, p, 1.0, 1.0) for p in (t.mean(0), (t[0] + t[1]) / 2, (t[1] + t[2]) / 2, (t[2] + t[0]) / 2)) < 0.01 for t in T])
        print("%s: %d of %d faces are the arm's surface (the rest are the cutter's faces: left out)" % (nm, on.sum(), len(T)), flush=True)
        cuts.append(dense(T[on], NP, rng))
    both = np.concatenate(cuts)
    S_sh = MT.sockets(MT.T2)
    def arm(rel):
        sc = B.sidecar(lib, rel); return tri_bvh(B.stl_tris(lib, rel, sc)), S_sh["Shoulder R"] @ G.M4(sc["fits"]["Shoulder R"])
    A_src = S_sh["Shoulder R"] @ G.M4(B.sidecar(lib, SRC)["fits"]["Shoulder R"])
    def place(rel):
        bvh, A_x = arm(rel); M0 = np.linalg.inv(A_x) @ A_src
        sb, Mb, rms = fit(both, bvh, M0)
        s1, M1, _ = fit(cuts[0], bvh, Mb); s2, M2, _ = fit(cuts[1], bvh, Mb)          # each alone, from the pair's fit
        c = both.mean(0); p1, p2 = M1[:3, :3] @ c + M1[:3, 3], M2[:3, :3] @ c + M2[:3, 3]
        agree = (float(np.linalg.norm(p1 - p2)), G.ang(M1, M2))
        return dict(rel=rel, share=sb, share1=s1, share2=s2, agree_mm=agree[0], agree_deg=agree[1], M=Mb, A=A_x,
                    ok=sb >= LAND and agree[0] <= AGREE_MM and agree[1] <= AGREE_DEG)
    ref = place(MT.ARM)
    print("2B R (the shell's reference): %.0f%% of the cuts land (alone %.0f%% / %.0f%%), cuts agree %.2f mm %.1f deg"
          % (100 * ref["share"], 100 * ref["share1"], 100 * ref["share2"], ref["agree_mm"], ref["agree_deg"]), flush=True)
    PadR = MT.sockets(MT.ARM)["Pad R"]; K = np.linalg.inv(ref["M"]) @ PadR           # the shell in Arm 1A R's own frame
    arms = []
    for p in sorted(glob.glob(os.path.join(lib, "Mar Fil - Tacticus", kit, "**", "*.sockets.json"), recursive=True)):
        rel = os.path.relpath(p, lib).replace("\\", "/")[:-13]; d = json.load(open(p, encoding="utf-8-sig"))
        if d.get("category") == "Arms" and "Shoulder R" in (d.get("exact") or []) and rel != MT.ARM: arms.append(rel)
    pick = rnd.sample(arms, N)
    pads = [r for r in json.load(open(os.path.join(outdir, "pads_plan.json"), encoding="utf-8"))["rows"] if r["joint"] == "Pad R"]
    pp = rnd.sample(pads, N); res = []
    for rel in pick:
        r = place(rel); r["pad"] = r["M"] @ K; res.append(r)
        print("%-40s %.0f%% land (cuts alone %.0f%% / %.0f%%), cuts agree %.2f mm %.1f deg -> %s" % (os.path.basename(rel), 100 * r["share"],
              100 * r["share1"], 100 * r["share2"], r["agree_mm"], r["agree_deg"], "MATCH" if r["ok"] else "NOT SURE"), flush=True)
    # render: Torso 2, the arm on it, a random pauldron on the arm's Pad R (its origin = the shell)
    import render as R
    for o in ob: o.hide_render = True
    cam = R.setup(420); sc = bpy.context.scene; outs, info = [], []
    tor = B.make_mesh("TORSO", B.stl_tris(lib, MT.T2, B.sidecar(lib, MT.T2)), np.eye(4)); sc.collection.objects.link(tor); tor.color = (0.72, 0.72, 0.74, 1)
    for k, (r, pr) in enumerate(zip(res, pp)):
        a = B.make_mesh("ARM", B.stl_tris(lib, r["rel"], B.sidecar(lib, r["rel"])), np.eye(4)); sc.collection.objects.link(a)
        a.matrix_world = G.mat(r["A"]); a.color = (0.72, 0.72, 0.74, 1)
        psc = B.sidecar(lib, pr["rel"]); po = B.make_mesh("PAD", B.stl_tris(lib, pr["rel"], psc), np.eye(4)); sc.collection.objects.link(po)
        po.matrix_world = G.mat(r["A"] @ r["pad"] @ G.M4(psc["fits"]["Pad R"])); po.color = (0.85, 0.55, 0.25, 1)
        bpy.context.view_layer.update()
        c = Vector(r["A"][:3, 3]) + Vector((2.0, 0, 3.0))
        for view, d in (("front", Vector((0.35, -1, 0.15))), ("side", Vector((1, -0.25, 0.15)))):
            d.normalize(); cam.data.ortho_scale = 30; cam.location = c + d * 200; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            p = os.path.join(outdir, "cs_%d_%s.png" % (k, view)); sc.render.filepath = p; bpy.ops.render.render(write_still=True); outs.append(p)
        for o in (a, po): bpy.data.objects.remove(o, do_unlink=True)
        info.append("%s on %s (%.0f%% of the cuts land)" % (pr["name"], os.path.basename(r["rel"]), 100 * r["share"]))
    ims = [bpy.data.images.load(p) for p in outs]
    px = [np.array(i.pixels[:]).reshape(i.size[1], i.size[0], 4) for i in ims]
    rows = [np.concatenate(px[k:k + 2], 1) for k in range(0, len(px), 2)]
    Aimg = np.concatenate(rows[::-1], 0)
    im = bpy.data.images.new("s", Aimg.shape[1], Aimg.shape[0]); im.pixels = Aimg.ravel(); im.filepath_raw = os.path.join(outdir, "cut_shape_showcase.png"); im.file_format = "PNG"; im.save()
    for k, s in enumerate(info): print("SHOW", k + 1, s, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except SystemExit as e: print("STOPPED:", e, flush=True)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
