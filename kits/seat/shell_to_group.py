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

CUT, SAME, CAP = 2.5, 0.06, 7.0


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
    types = []
    for i in sorted((i for i in by if i.endswith("_shell")), key=lambda i: int(i[1:-6])):
        t = i[:-6]
        if t + "_arm" not in by or t not in by: continue
        sh, arm = by[i], by[t + "_arm"]; rel = arm["kb_rel"]
        rider = by.get(t + "_pad"); crown = B.own(sh) @ (G.M4(rider["kb_on_frame"]) if rider else np.eye(4))
        PA = np.linalg.inv(B.own(arm)) @ crown                                   # Pad R in the type arm's own frame
        TA = own_tris(arm); C = TA.mean(1); N = np.cross(TA[:, 1] - TA[:, 0], TA[:, 2] - TA[:, 0])
        N /= np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
        Ts = own_tris(sh); M = np.linalg.inv(B.own(arm)) @ B.own(sh); bs = tri_bvh(Ts @ M[:3, :3].T + M[:3, 3])
        c0, z0 = PA[:3, 3], PA[:3, 2]
        near = np.array([(bs.find_nearest(Vector(c), CUT + 1)[3] or 99.0) for c in C]) <= CUT
        for rad in (CAP, CAP * 1.3, CAP * 1.7):                               # the shoulder cap only (Nov 28): under the
            m = near & (np.linalg.norm(C - c0, axis=1) <= rad) & (N @ z0 > 0.2)  # crown, facing out at the shell
            if m.sum() >= 150: break
        P = C[m]; P = P[np.linspace(0, len(P) - 1, min(len(P), 900)).astype(int)]
        types.append(dict(col=t, rel=rel, PA=PA, P=P, A=S_sh["Shoulder R"] @ G.M4(B.sidecar(lib, rel)["fits"]["Shoulder R"]), members=[]))
        print("type %-5s %-52s cap cut %d points" % (t, os.path.basename(rel)[:52], len(P)), flush=True)
    trel = {ty["rel"] for ty in types}
    turns = [np.eye(3)] + [G.rot(ax, a) for ax in ((1, 0, 0), (0, 1, 0), (0, 0, 1)) for a in (-40, -20, 20, 40)]

    def fit(ty, bvh, A_B, many):
        M0 = np.linalg.inv(A_B) @ ty["A"]; c = M0[:3, :3] @ ty["P"].mean(0) + M0[:3, 3]
        starts = []
        for R in (turns if many else turns[:1] + [G.rot((0, 0, 1), a) for a in (-30, 30)] + [G.rot((1, 0, 0), a) for a in (-30, 30)]):
            Rf = R @ M0[:3, :3]; starts.append((Rf, R @ (M0[:3, 3] - c) + c))
        Pc = ty["P"][::3]
        co = sorted((G.icp(bvh, Pc, R0, t0, iters=10, keep=0.8, lim=6.0) for R0, t0 in starts), key=lambda f: f[2])[:2]
        best = min((G.icp(bvh, ty["P"], R, t, iters=30, keep=0.8, lim=3.0) for R, t, _r in co), key=lambda f: f[2])
        Mf = np.eye(4); Mf[:3, :3], Mf[:3, 3] = best[0], best[1]; return best[2], Mf

    left = []
    for n, b in enumerate(a for a in arms if a not in trel):
        sc = B.sidecar(lib, b); bvh = tri_bvh(B.stl_tris(lib, b, sc)); A_B = S_sh["Shoulder R"] @ G.M4(sc["fits"]["Shoulder R"])
        got = None
        for pool, many in (([ty for ty in types if kit_of(ty["rel"]) == kit_of(b)], True),
                           ([ty for ty in types if ty["rel"].split("/")[0] == b.split("/")[0] and kit_of(ty["rel"]) != kit_of(b)], False)):
            for ty in pool:
                rms, Mf = fit(ty, bvh, A_B, many)
                if got is None or rms < got[0]: got = (rms, Mf, ty)
            if got and got[0] < SAME: break
        if got is None: left.append(dict(rel=b, rms=None, near=None)); continue
        rms, Mf, ty = got
        if rms < SAME: ty["members"].append(dict(rel=b, rms=round(rms, 4), pad=G.flat16(Mf @ ty["PA"]), A=G.flat16(A_B)))
        else: left.append(dict(rel=b, rms=round(rms, 4), near=ty["rel"]))
        if n % 50 == 0: print("  %d arms, %d matched so far" % (n, sum(len(t["members"]) for t in types)), flush=True)
    res = [dict(col=ty["col"], rel=ty["rel"], cut=len(ty["P"]), members=ty["members"]) for ty in types]
    for ty in types: print("%-5s %-52s takes %d arms" % (ty["col"], os.path.basename(ty["rel"])[:52], len(ty["members"])), flush=True)
    json.dump(dict(types=res, left=left), open(out.replace(".json", "_left.json"), "w", encoding="utf-8"), indent=1)
    import collections
    kl = collections.Counter(kit_of(l["rel"]) for l in left); ka = collections.Counter(kit_of(a) for a in arms if a not in trel)
    print("\nNOT MATCHED, by kit (arms left / arms in kit):")
    for k, v in sorted(kl.items(), key=lambda kv: -kv[1]): print("  %3d / %3d  %s" % (v, ka[k], k))
    json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
    n_ok = sum(len(r["members"]) for r in res)
    print("ALL: %d of %d arms take a type's shell by shoulder shape (under %.2f mm); %d left" % (n_ok, n_ok + len(left), SAME, len(left)), flush=True)
    if "--render" in A:
        k = A.index("--render"); render(by, res, int(A[k + 1]), int(A[k + 2]), os.path.dirname(out))


def fill(A):
    """every right arm a Pad R (Josh, Nov 28: "This needs to get to a 100 percent success rate"): the same-shoulder
    carry where the shape matched (main); every other arm takes its kit's type (the one whose Shoulder R pose is
    nearest, so raised arms go with raised; no type in the kit: the maker's nearest) at the same place on the torso,
    slid along the shell's +Z until it touches this arm's shoulder as it touches the type arm's"""
    import collections
    src, gj, out = A[1], A[2], A[3]; lib = MT.LIB
    G0 = json.load(open(gj.replace(".json", "_left.json"), encoding="utf-8"))
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False); bpy.context.view_layer.update()
    by = {o["kb_id"]: o for o in bpy.data.objects if "kb_id" in o}; S_sh = MT.sockets(MT.T2)
    sys.path.insert(0, HERE); import shell_on_arms as SO
    types = {}
    for ty in G0["types"]:
        t = ty["col"]; sh, arm, tor = by[t + "_shell"], by[t + "_arm"], by[t]
        rider = by.get(t + "_pad"); crown = B.own(sh) @ (G.M4(rider["kb_on_frame"]) if rider else np.eye(4))
        Vs = SO.own_tris(sh).reshape(-1, 3); Vs = Vs[np.linspace(0, len(Vs) - 1, 2500).astype(int)]
        Ki = np.linalg.inv(G.M4(sh["kb_own_in_obj"])) ; Vc = Vs                                     # shell points in its own frame
        Cr = np.linalg.inv(B.own(sh)) @ crown; Vc = (Vs - Cr[:3, 3]) @ Cr[:3, :3]                    # ... in the crown frame
        Sh_t = np.linalg.inv(B.own(tor)) @ crown                                                     # the shell on the torso
        A_A = S_sh["Shoulder R"] @ G.M4(B.sidecar(lib, ty["rel"])["fits"]["Shoulder R"])
        lvl = SO.level(SO.tri_bvh(SO.own_tris(arm)), Vc, np.linalg.inv(B.own(arm)) @ crown, 0.0)
        types[t] = dict(ty, Sh_t=Sh_t, A_A=A_A, Vc=Vc, lvl=lvl)
    for ty in types.values():
        for m in ty["members"]: m["tier"] = "shape"
    rows = []
    for l in G0["left"]:
        b = l["rel"]; sc = B.sidecar(lib, b); A_B = S_sh["Shoulder R"] @ G.M4(sc["fits"]["Shoulder R"])
        pool = [ty for ty in types.values() if kit_of(ty["rel"]) == kit_of(b)] or [ty for ty in types.values() if ty["rel"].split("/")[0] == b.split("/")[0]]
        ty = min(pool, key=lambda ty: G.ang(ty["A_A"], A_B))
        M = np.linalg.inv(A_B) @ ty["Sh_t"]; bvh = SO.tri_bvh(B.stl_tris(lib, b, sc))
        f = lambda h: SO.level(bvh, ty["Vc"], M, h) - ty["lvl"]; lo, hi = -SO.LIM, SO.LIM; flo, fhi = f(lo), f(hi)
        if flo > 0: h, note = lo, "still clear at -4 mm"
        elif fhi < 0: h, note = hi, "still in the arm at +4 mm"
        else:
            for _ in range(22):
                mid = (lo + hi) / 2
                if f(mid) < 0: lo = mid
                else: hi = mid
            h, note = (lo + hi) / 2, ""
        L = M @ np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, h], [0, 0, 0, 1.0]])
        ty["members"].append(dict(rel=b, rms=l["rms"], pad=G.flat16(L), A=G.flat16(A_B), tier="kit", lift=round(h, 3), note=note,
                                  pose_deg=round(G.ang(ty["A_A"], A_B), 1)))
        rows.append((b, ty["rel"], h, note))
    res = [{k: v for k, v in ty.items() if k in ("col", "rel", "cut", "members")} for ty in types.values()]
    json.dump(res, open(out, "w", encoding="utf-8"), indent=1)
    n1 = sum(1 for r in res for m in r["members"] if m["tier"] == "shape"); n2 = sum(1 for r in res for m in r["members"] if m["tier"] == "kit")
    print("every right arm placed: %d your arm types, %d by the same shoulder, %d by their kit's type + touch; %d at the slide limit"
          % (len(res), n1, n2, sum(1 for r in rows if r[3])), flush=True)
    for b, t, h, note in rows:
        if note: print("  LIMIT %-60s from %s: %s" % (os.path.basename(b)[:60], os.path.basename(t), note))
    if "--render" in A:
        k = A.index("--render"); render(by, res, int(A[k + 1]), int(A[k + 2]), os.path.dirname(out))


def render(by, res, N, seed, outdir):
    import render as R
    lib = MT.LIB; rnd = random.Random(seed)
    plan = os.path.join(outdir, "pads_plan.json")
    pads = [r for r in json.load(open(plan, encoding="utf-8"))["rows"] if r["joint"] == "Pad R"]
    pool = [(r, m) for r in res for m in r["members"]]
    tiers = sorted({m.get("tier", "shape") for r, m in pool})
    picks = []
    for k, tr in enumerate(tiers):
        tp = [x for x in pool if x[1].get("tier", "shape") == tr]; want = N // len(tiers) + (1 if k < N % len(tiers) else 0)
        picks += rnd.sample(tp, min(want, len(tp)))
    pp = rnd.sample(pads, len(picks))
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
        info.append("%s on %s (from %s; %s)" % (pr["name"], os.path.basename(m["rel"]), os.path.basename(r["rel"]),
                    "same shoulder, fit %.3f mm" % m["rms"] if m.get("tier", "shape") == "shape" else "kit type's shell on the torso, slid %+.2f mm to touch" % m["lift"]))
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
    try: fill(A) if A[0] == "fill" else main(A)
    except SystemExit as e: print("STOPPED:", e, flush=True)
    except BaseException: import traceback; traceback.print_exc(); sys.stdout.flush(); os._exit(1)
    finally: sys.stdout.flush(); os._exit(0)
