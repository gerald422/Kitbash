"""Compare rock objectives: 68 fit from legs 29 moved to legs 35 (truth: best-seated pose there),
and the new families' upright starting poses (should barely move)."""
exec(open("/home/claude/test/variants/common.py").read())
from mathutils.bvhtree import BVHTree
select(None)
legs29 = send(f"{MF}/Kit/Legs/29-Legs-2.stl", "Legs", (0, 0, 0)); a29 = shin_anchors(legs29, "29-Legs-2")
legs35 = send(f"{MF}/Kit/Legs/35-Legs-2-A.stl", "Legs", (80, 0, 0)); a35 = shin_anchors(legs35, "35-Legs-2-A")
deps = bpy.context.evaluated_depsgraph_get()
def load(rel):
    bpy.ops.wm.stl_import(filepath=os.path.join(LIB, rel)); return vl.objects.active
def unit(M):
    loc, rot, _ = M.decompose(); return Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))
def objective(kind):
    def f(sd):
        seen = sd < 9.0
        if seen.sum() < max(5, len(sd) // 4): return 1e9
        if kind == "orig":
            s = sd.copy(); s[~seen] = 2.0
        else:
            s = sd - np.percentile(sd[seen], 5); s[~seen] = 2.0
        cut = np.clip(-s, 0, None)
        if kind in ("orig", "near"):
            gap = np.clip(s, 0, 2.0); near = np.sort(gap)[:max(1, len(gap) // 3)]
            return 25 * cut.mean() + near.mean() + 0.2 * gap.mean()
        if kind == "mean":
            return 25 * cut.mean() + np.clip(s, 0, 3.0).mean()
        if kind == "median":
            return 25 * cut.mean() + np.median(np.clip(s, 0, 3.0))
    return f
def rock(part, legs, anchor, kind, span=15.0, middle=4.0):
    pv, pt = T._world_tris(part, deps)
    Aw = unit(anchor.matrix_world); A_ = np.array(Aw.to_3x3()); piv = np.array(Aw.translation)
    inner = T.inner_side(pv, pt, A_, piv, middle, 220)
    tree = BVHTree.FromObject(legs, deps); inv = np.array(legs.matrix_world.inverted())
    def signed(W):
        Lh = W @ inv[:3, :3].T + inv[:3, 3]; out = np.full(len(W), 9.0)
        for i, q in enumerate(Lh):
            h = tree.find_nearest(Vector(q), 5.0)
            if h[0] is not None: out[i] = (Vector(q) - h[0]).dot(h[1])
        return out
    R3 = lambda ax, d: np.array(Matrix.Rotation(math.radians(d), 3, Vector(ax)))
    f = objective(kind)
    best_R = np.eye(3); best = f(signed(inner))
    for sp, st in ((span, span / 6.0), (span / 6.0, span / 30.0)):
        base = best_R.copy()
        for a in np.arange(-sp, sp + 1e-9, st):
            for b in np.arange(-sp, sp + 1e-9, st):
                Rw = A_ @ (R3((1, 0, 0), a) @ R3((0, 1, 0), b)) @ A_.T @ base
                sc = f(signed((inner - piv) @ Rw.T + piv))
                if sc < best - 1e-9: best, best_R = sc, Rw
    M3 = Matrix(best_R.tolist()).to_4x4()
    part.matrix_world = Matrix.Translation(Vector(piv)) @ M3 @ Matrix.Translation(-Vector(piv)) @ part.matrix_world
    T.settle_onto(part, [legs], Aw.to_3x3() @ Vector((0, 0, -1)), sink=0.2, band=(Aw.translation, Aw.to_3x3() @ Vector((1, 0, 0)), 0.5 * middle))
    return math.degrees(Matrix(best_R.tolist()).to_quaternion().angle)
p68 = load(f"{MF}/Kit/Knee Pads/68-ShinPad-1.stl")
pB = load(f"{MF}/Kit B/Knee Pads/29-Shin-Pad-1.stl")
pM = {"R": load(f"{MA}/Kit/ShinPads-RawSTL/Chin_pad_2_R.stl"), "L": load(f"{MA}/Kit/ShinPads-RawSTL/Chin_pad_2_L.stl")}
for kind in ("orig", "near", "mean", "median"):
    res = []
    for side in ("R", "L"):
        fit = unit(a29[side].matrix_world).inverted() @ legs29.matrix_world @ Matrix(CLICKS["29-Legs-2"][side]["seated"])
        p68.matrix_world = unit(a35[side].matrix_world) @ fit
        truth = legs35.matrix_world @ Matrix(CLICKS["35-Legs-2-A"][side]["seated"])
        e0 = ang(p68.matrix_world, truth)
        rk = rock(p68, legs35, a35[side], kind)
        res.append(f"68@35{side}: {e0:4.1f}->{ang(p68.matrix_world, truth):4.1f} (rock {rk:4.1f})")
    for side in ("R", "L"):
        byeye_shin(pB, legs29, a29[side], "marfilB", stage=0)
        res.append(f"B@29{side} rock {rock(pB, legs29, a29[side], kind):4.1f}")
        byeye_shin(pM[side], legs29, a29[side], "marta", stage=0)
        res.append(f"Marta@29{side} rock {rock(pM[side], legs29, a29[side], kind):4.1f}")
    print(f"{kind:7s}", " | ".join(res))
