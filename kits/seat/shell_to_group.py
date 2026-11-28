"""Josh's shell on each arm type carried to the other arms of its group by the shoulder's shape (Nov 28).

    BL kits/seat/shell_to_group.py -- ARM_TYPES.blend OUT.json [--render N SEED]
  BL = blender --background --factory-startup --python

For each column (an arm type with the shell where Josh set it): the arm's own surface under the shell (within CUT mm
of the shell's surface) is the shoulder cut, taken automatically. It is fitted by trimmed ICP onto every other written
right arm of the same kit (and the arms match_arm_types.py graded "same" to a seeded type), from where that arm sits
on the torso. Under SAME mm the shoulder is the same sculpt and the shell goes across with the fit (Pad R on that arm);
the rest are listed. --render: N random pauldrons on N random arms that took the shell, placed from the library as the
Squad Builder will (pauldron origin on the arm's Pad R), front and side, into OUT's folder as group_showcase.png."""
import os, sys, json, glob, random
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (REPO, HERE, os.path.join(REPO, "kits", "connectors")): sys.path.insert(0, p)
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import geom as G, batch as B, make_torso_batch as MT

CUT, SAME = 2.0, 0.06


def tri_bvh(T): return BVHTree.FromPolygons([tuple(v) for v in T.reshape(-1, 3)], [(3 * k, 3 * k + 1, 3 * k + 2) for k in range(len(T))])
def own_tris(o):
    Ki = np.linalg.inv(G.M4(o["kb_own_in_obj"])); return G.tris(o) @ Ki[:3, :3].T + Ki[:3, 3]
def kit_of(rel):
    p = rel.split("/"); return "/".join(p[:3] if p[0].startswith("Marta") else p[:2])


def main(A):
    src, out = A[0], A[1]; lib = MT.LIB
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}
    S_sh = MT.sockets(MT.T2)
    arms = []
    for p in sorted(glob.glob(os.path.join(lib, "*", "**", "*.sockets.json"), recursive=True)):
        rel = os.path.relpath(p, lib).replace("\\", "/")[:-13]
        if rel.startswith("_"): continue
        d = json.load(open(p, encoding="utf-8-sig"))
        if d.get("category") == "Arms" and not d.get("noPad") and "Shoulder R" in (d.get("exact") or []): arms.append(rel)
    same_to = {}
    tj = os.path.join(os.path.dirname(out), "arm_types.json")
    if os.path.exists(tj):
        for r in json.load(open(tj, encoding="utf-8"))["arms"]:
            if r["grade"] == "same" and not r["left"]: same_to.setdefault(r["type"], []).append(r["rel"])
    res = []
    for i in sorted((i for i in by if i.endswith("_shell")), key=lambda i: int(i[1:-6])):
        t = i[:-6]
        if t + "_arm" not in by or t not in by: continue
        sh, arm, tor = by[i], by[t + "_arm"], by[t]; rel = arm["kb_rel"]
        rider = by.get(t + "_pad"); crown = B.own(sh) @ (G.M4(rider["kb_on_frame"]) if rider else np.eye(4))
        PA = np.linalg.inv(B.own(arm)) @ crown                                   # Pad R in the type arm's own frame
        TA = own_tris(arm); C = TA.mean(1)
        Ts = own_tris(sh); M = np.linalg.inv(B.own(arm)) @ B.own(sh); Ts = Ts @ M[:3, :3].T + M[:3, 3]
        bs = tri_bvh(Ts); P = None
        for cut in (CUT, CUT * 1.75):
            d = np.array([(bs.find_nearest(Vector(c), cut + 1)[3] or 99.0) for c in C]); P = C[d <= cut]
            if len(P) >= 150: break
        P = P[np.linspace(0, len(P) - 1, min(len(P), 900)).astype(int)]
        A_A = S_sh["Shoulder R"] @ G.M4(B.sidecar(lib, rel)["fits"]["Shoulder R"])
        cands = sorted(set(a for a in arms if kit_of(a) == kit_of(rel) and a != rel) |
                       set(a for a in same_to.get(arm.name.replace(" (locked)", ""), []) if a != rel))
        mem = []
        for b in cands:
            sc = B.sidecar(lib, b); T = B.stl_tris(lib, b, sc)
            A_B = S_sh["Shoulder R"] @ G.M4(sc["fits"]["Shoulder R"]); M0 = np.linalg.inv(A_B) @ A_A
            R, tt, rms = G.icp(tri_bvh(T), P, M0[:3, :3], M0[:3, 3], iters=30, keep=0.8, lim=3.0)
            Mf = np.eye(4); Mf[:3, :3] = R; Mf[:3, 3] = tt
            mem.append(dict(rel=b, rms=round(rms, 4), pad=G.flat16(Mf @ PA), A=G.flat16(A_B), moved=round(float(np.linalg.norm((Mf @ PA)[:3, 3] - (M0 @ PA)[:3, 3])), 2)))
        ok = [m for m in mem if m["rms"] < SAME]
        res.append(dict(col=t, rel=rel, cut=len(P), members=mem))
        print("%-5s %-52s cut %4d; same shoulder %3d of %3d in its kit" % (t, os.path.basename(rel)[:52], len(P), len(ok), len(mem)), flush=True)
    json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
    n_ok = sum(1 for r in res for m in r["members"] if m["rms"] < SAME); n = sum(len(r["members"]) for r in res)
    print("ALL: %d of %d arms take a type's shell by shoulder shape (under %.2f mm)" % (n_ok, n, SAME), flush=True)
    if "--render" in A:
        k = A.index("--render"); render(by, res, int(A[k + 1]), int(A[k + 2]), os.path.dirname(out))


def render(by, res, N, seed, outdir):
    import render as R
    lib = MT.LIB; rnd = random.Random(seed)
    plan = os.path.join(outdir, "pads_plan.json")
    pads = [r for r in json.load(open(plan, encoding="utf-8"))["rows"] if r["joint"] == "Pad R"]
    pool = [(r, m) for r in res for m in r["members"] if m["rms"] < SAME]
    picks = rnd.sample(pool, min(N, len(pool))); pp = rnd.sample(pads, len(picks))
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = True; o.color = (0.72, 0.72, 0.74, 1)
    cam = R.setup(420); sc = bpy.context.scene; outs, info = [], []
    for (r, m), pr in zip(picks, pp):
        tor = by[r["col"]]; tor.hide_render = False
        W_arm = B.own(tor) @ G.M4(m["A"])
        asc = B.sidecar(lib, m["rel"]); ao = B.make_mesh("ARM", B.stl_tris(lib, m["rel"], asc), np.eye(4)); sc.collection.objects.link(ao)
        ao.matrix_world = G.mat(W_arm); ao.color = (0.72, 0.72, 0.74, 1)
        psc = B.sidecar(lib, pr["rel"]); po = B.make_mesh("PAD", B.stl_tris(lib, pr["rel"], psc), np.eye(4)); sc.collection.objects.link(po)
        po.matrix_world = G.mat(W_arm @ G.M4(m["pad"]) @ G.M4(psc["fits"]["Pad R"])); po.color = (0.85, 0.55, 0.25, 1)
        bpy.context.view_layer.update()
        c = Vector(B.own(tor)[:3, 3]) + Vector((10.0, 0, 28))
        for view, d in (("front", Vector((0.35, -1, 0.15))), ("side", Vector((1, -0.25, 0.15)))):
            d.normalize(); cam.data.ortho_scale = 38; cam.location = c + d * 200; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
            p = os.path.join(outdir, "grp_%d_%s.png" % (len(info), view)); sc.render.filepath = p; bpy.ops.render.render(write_still=True); outs.append(p)
        for o in (ao, po): bpy.data.objects.remove(o, do_unlink=True)
        tor.hide_render = True
        info.append("%s on %s (its type: %s; shoulder fit %.3f mm)" % (pr["name"], os.path.basename(m["rel"]), os.path.basename(r["rel"]), m["rms"]))
    ims = [bpy.data.images.load(p) for p in outs]
    px = [np.array(i.pixels[:]).reshape(i.size[1], i.size[0], 4) for i in ims]
    pairs = [np.concatenate(px[k:k + 2], 1) for k in range(0, len(px), 2)]
    rows = [np.concatenate(pairs[k:k + 2], 1) for k in range(0, len(pairs), 2)]
    A = np.concatenate(rows[::-1], 0)
    im = bpy.data.images.new("s", A.shape[1], A.shape[0]); im.pixels = A.ravel(); im.filepath_raw = os.path.join(outdir, "group_showcase.png"); im.file_format = "PNG"; im.save()
    for k, s in enumerate(info): print("SHOW", k + 1, s, flush=True)


if __name__ == "__main__":
    A = sys.argv[sys.argv.index("--") + 1:]
    sys.stdout.reconfigure(encoding="utf-8")
    try: main(A)
    except SystemExit as e: print("STOPPED:", e, flush=True)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
