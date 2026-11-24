"""Pads: the pauldron guide (the pad connector) seated on an arm, inside Blender. Moved from the Nov 23 scripts
(seat_live6, seat_rest, profile, swing, joint_seat, joint_run2); behaviour unchanged, objects are arguments.

The guide's frame: origin on its crown, +Z out, +Y front; its dome centre is CROWN mm under the crown. The pad sits in
the guide (the pad is the guide's mesh child). "Seating a guide" moves the guide (and so its pad) onto an arm: that is
the arm's `Pad R` socket (stage 4). What works (skill `kitbash-seat-by-shape`):
  outline_seat  same-shape transfer: the arm surface the pad sees from inside, fitted by ICP onto the reference arm's
  joint_seat    carried by the shoulder joint: keep the reference pad's angle to the joint axis, sweep only the turn
                about the joint, then rest-fit a small move (top rests ~0.3 mm, rim clear evenly)
  joint_seat_held   the same with the turn held near the arm file's own (+-lim) and a small free nudge after
Raised arms (the Chaplains) fail: by-eye jobs."""
import math
import numpy as np
from mathutils import Matrix, Vector
import geom as G

CROWN, CONE = 4.04, 75.0
CROWN_T = 0.3        # mm: the pad's inside top rests this far off the shoulder
DEEP_W = 4.0         # weight of points sunk into the arm


def pad_of(guide):
    """the pad mesh parented in the guide"""
    return next(o for o in guide.children if o.type == 'MESH')


def outline(b, c, ax):
    """what the pad sees: first ray hits aimed in at the shoulder from every direction within CONE deg of the axis"""
    ax = ax / np.linalg.norm(ax); x = np.cross([0.31, 0.71, 0.63], ax); x /= np.linalg.norm(x); y = np.cross(ax, x)
    pts = []
    for th in np.radians(np.arange(0, CONE + 0.1, 3.0)):
        for ph in np.radians(np.arange(0, 360, 6 if th > 0 else 360)):
            u = math.cos(th) * ax + math.sin(th) * (math.cos(ph) * x + math.sin(ph) * y)
            loc, nor, _i, _d = b.ray_cast(Vector(c + u * 30), Vector(-u), 40.0)
            if loc is not None and nor.dot(Vector(u)) > 0: pts.append(tuple(loc))
    return np.array(pts)


def outline_seat(arm, guide, ref_arm, ref_guide_M, out=(1.0, 0, 0), front=(0, 1.0, 0), starts=(), seed=3):
    """Seat `guide` on `arm` by the outline of `ref_arm` under its guide (ref_guide_M, world). out / front: this arm
    file's facing (Mar Fil, TN, Marta: +X / +Y; Springles arms.blend: +Y / -X). starts: extra start poses (world).
    Moves the guide; returns a log dict (fit_mm: trimmed rms of the outline, lower is better)."""
    M0 = G.M4(ref_guide_M); c0, ax0 = M0[:3, 3] - CROWN * M0[:3, 2], M0[:3, 2]
    P0 = outline(G.bvh(ref_arm), c0, ax0)
    P = P0[np.random.default_rng(seed).choice(len(P0), min(700, len(P0)), replace=False)]
    outv, frontv = np.array(out, float), np.array(front, float); b = G.bvh(arm)
    Ms = [G.M4(s) for s in starts] + [np.array(guide.matrix_world)]
    for Mb in list(Ms):                                   # each start also turned about its axis so +X faces out
        z = Mb[:3, 2]; xo = outv - (outv @ z) * z
        if np.linalg.norm(xo) > 1e-6:
            xo /= np.linalg.norm(xo); x0 = Mb[:3, 0]
            a = math.degrees(math.atan2(np.cross(x0, xo) @ z, x0 @ xo))
            Mr = Mb.copy(); cz = Mb[:3, 3] - CROWN * z; Rr = G.rot(z, a)
            Mr[:3, :3] = Rr @ Mb[:3, :3]; Mr[:3, 3] = cz + Rr @ (Mb[:3, 3] - cz); Ms.append(Mr)
    fits = []
    for Mst in Ms:
        cs, axs = Mst[:3, 3] - CROWN * Mst[:3, 2], Mst[:3, 2]
        for tilt in ((0, 0), (20, 0), (-20, 0), (0, 20), (0, -20)):
            for roll in (0, 30, -30):
                Rp = G.rot(axs, roll) @ G.rot(Mst[:3, 0], tilt[0]) @ G.rot(Mst[:3, 1], tilt[1])
                Ms2 = np.eye(4); Ms2[:3, :3] = Rp @ Mst[:3, :3]; Ms2[:3, 3] = cs + Rp @ (Mst[:3, 3] - cs)
                T = Ms2 @ np.linalg.inv(M0)
                R2, t2, res = G.icp(b, P, T[:3, :3], T[:3, 3])
                A = R2 @ M0[:3, :3]
                if A[:, 0] @ outv > 0.7 and A[:, 1] @ frontv > 0.5: fits.append((res, R2, t2))
    if not fits: return dict(arm=arm.name, note="no fit facing out/front: left as it was")
    fits.sort(key=lambda f: f[0]); res, R, t = fits[0]
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t; guide.matrix_world = G.mat(T @ M0)
    return dict(arm=arm.name, fit_mm=round(res, 3), next=[round(f[0], 3) for f in fits[1:3]], starts_ok=len(fits))


# ---- rest and clear (how Josh places pads: the inside top rests, the rim stands clear evenly, nothing inside)

def setup(arm, guide):
    """(arm BVH, the pad's inside points in the guide's frame)"""
    b = G.bvh(arm); Mad = np.array(guide.matrix_world); Pin = G.part_inside(pad_of(guide))
    return b, (Pin - Mad[:3, 3]) @ Mad[:3, :3]


def prep(Ploc, n=900, seed=5):
    rng = np.random.default_rng(seed); P = Ploc[rng.choice(len(Ploc), min(n, len(Ploc)), replace=False)]
    r = np.hypot(P[:, 0], P[:, 1]); rmax = np.percentile(r, 98)
    band = np.digitize(r / rmax, [0.35, 0.75]); sec = ((np.degrees(np.arctan2(P[:, 1], P[:, 0])) + 22.5) % 360 // 45).astype(int)
    return P, band, sec


def rest_cost(b, PP, R, t, parts=False, deep_w=DEEP_W):
    P, band, sec = PP
    _N, d, ins = G.probe(b, P @ R.T + t, 4.0); ok = d < 9
    if ok.mean() < 0.6: return (9.0, {}) if parts else 9.0
    g = np.where(ins, -d, d)
    cm = ok & (band == 0)
    crown = float(np.percentile(g[cm], 30)) if cm.sum() > 5 else 3.0
    rims = [np.median(g[ok & (band == 2) & (sec == s)]) for s in range(8) if (ok & (band == 2) & (sec == s)).sum() >= 4]
    mids = [np.median(g[ok & (band == 1) & (sec == s)]) for s in range(8) if (ok & (band == 1) & (sec == s)).sum() >= 4]
    deep = float((g[ok] < -0.15).mean())
    rim_low = float(np.clip(0.6 - np.array(rims), 0, None).sum()) if rims else 3.0
    c = abs(crown - CROWN_T) + deep_w * deep + float(np.std(rims)) + 0.5 * float(np.std(mids)) + rim_low + 2.0 * (1 - ok.mean())
    if parts: return c, dict(crown=round(crown, 2), deep=round(deep, 3), rim_std=round(float(np.std(rims)), 2),
                             mid_std=round(float(np.std(mids)), 2), rims=np.round(rims, 1).tolist())
    return c


def profile(b, Ploc, M):
    """gap profile: 3 bands (crown / mid / rim) x 8 sectors (0 = +X outside, 90 = +Y front), median gap, mm"""
    Q = Ploc @ M[:3, :3].T + M[:3, 3]; _N, d, ins = G.probe(b, Q, 4.0); ok = d < 9; g = np.where(ins, -d, d)
    r = np.hypot(Ploc[:, 0], Ploc[:, 1]); rmax = np.percentile(r, 98)
    band = np.digitize(r / rmax, [0.35, 0.75]); sec = ((np.degrees(np.arctan2(Ploc[:, 1], Ploc[:, 0])) + 22.5) % 360 // 45).astype(int)
    out = np.full((3, 8), np.nan)
    for bb in range(3):
        for s in range(8):
            m = ok & (band == bb) & (sec == s)
            if m.sum() >= 3: out[bb, s] = np.median(g[m])
    return out


def nudge_rest(b, PP, R, t, steps=(4.0, 2.0, 1.0, 0.5), mm=(0.4, 0.2, 0.1, 0.05)):
    """free rest step: small turns about the part's own axes and moves, keeping the best rest_cost"""
    best = rest_cost(b, PP, R, t)
    for sd, sm in zip(steps, mm):
        improved = True
        while improved:
            improved = False
            for k in range(6):
                for sgn in (1, -1):
                    pivot = t - 4.0 * R[:, 2]
                    if k < 3:
                        Rr = G.rot(R[:, k], sgn * sd); R2 = Rr @ R; t2 = pivot + Rr @ (t - pivot)
                    else: R2 = R; t2 = t + R[:, k - 3] * sgn * sm
                    c = rest_cost(b, PP, R2, t2)
                    if c < best - 1e-4: best, R, t, improved = c, R2, t2, True
    return R, t, best


def _slide(b, PP, R, t, steps):
    best = rest_cost(b, PP, R, t)
    for sm in steps:
        imp = True
        while imp:
            imp = False
            for k in range(3):
                for sg in (1, -1):
                    t2 = t + np.eye(3)[k] * sg * sm; cc = rest_cost(b, PP, R, t2)
                    if cc < best - 1e-4: best, t, imp = cc, t2, True
    return t, best


# ---- the shoulder joint (the arm's joint flat) carries the pad

def fframe(c, n):
    z = n / np.linalg.norm(n); u = np.array([0, 0, 1.0]) - z[2] * z; u /= np.linalg.norm(u); x = np.cross(u, z)
    F = np.eye(4); F[:3, 0], F[:3, 1], F[:3, 2], F[:3, 3] = x, u, z, c; return F


def joint_flat(arm, guide_M, lim=0.5):
    """(centre, normal) of the arm's shoulder joint flat: the biggest flat near the guide, facing away from its outside"""
    crown = guide_M[:3, 3]; xo = guide_M[:3, 0]
    c = [(a, c, n) for c, n, a in G.flat_patches(arm, top=8) if np.linalg.norm(c - crown) < 6.5 and n @ -xo > lim]
    c.sort(key=lambda f: -f[0]); return (c[0][1], c[0][2]) if c else None


def jframe(arm, guide): return fframe(*joint_flat(arm, np.array(guide.matrix_world)))


def roll_about(F, th):
    n = F[:3, 2]; c = F[:3, 3]; R = np.array(Matrix.Rotation(math.radians(th), 4, Vector(n))); R[:3, 3] = c - R[:3, :3] @ c; return R


def joint_seat(arm, guide, ref_arm, ref_guide, step=5):
    """Josh's pad on ref_arm carried to arm by the joint: full turn sweep about the joint axis, rest-fit move, fine turn.
    Returns (T guide world, turn, cost, parts, X = the joint's carry: put the reference torso on with X @ torso)."""
    b, Ploc = setup(arm, guide); PP = prep(Ploc, 700); Ft = jframe(arm, guide); Fr = jframe(ref_arm, ref_guide)
    B = Ft @ np.linalg.inv(Fr); Mr = np.array(ref_guide.matrix_world); res = []
    for th in np.arange(0, 360, step):
        M = roll_about(Ft, th) @ B @ Mr; R, t = M[:3, :3], M[:3, 3]; t, best = _slide(b, PP, R, t, (0.8, 0.4, 0.2, 0.1))
        T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t; res.append((best, float(th), T))
    res.sort(key=lambda r: r[0]); c, th, T = res[0]
    for th2 in np.arange(th - 4, th + 4.1, 1.0):
        M = roll_about(Ft, th2) @ B @ Mr; R, t = M[:3, :3], M[:3, 3]; t, best = _slide(b, PP, R, t, (0.4, 0.2, 0.1, 0.05))
        if best < c: c, th = best, float(th2); T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t
    _, parts = rest_cost(b, PP, T[:3, :3], T[:3, 3], True)
    return T, th, c, parts, roll_about(Ft, th) @ B


def _tnudge(b, PP, R, t, rmax=8.0):
    best = rest_cost(b, PP, R, t); R0 = R.copy()
    for sd, sm in zip((2.0, 1.0, 0.5), (0.2, 0.1, 0.05)):
        imp = True
        while imp:
            imp = False
            for k in range(6):
                for sg in (1, -1):
                    if k < 3:
                        if k == 2: continue                       # no spin about the pad's own axis
                        pv = t - 4.0 * R[:, 2]; Rr = G.rot(R[:, k], sg * sd); R2 = Rr @ R; t2 = pv + Rr @ (t - pv)
                        if G.ang(R0, R2) > rmax: continue
                    else: R2 = R; t2 = t + np.eye(3)[k - 3] * sg * sm
                    c = rest_cost(b, PP, R2, t2)
                    if c < best - 1e-4: best, R, t, imp = c, R2, t2, True
    return R, t, best


def joint_seat_held(arm, guide, ref_arm, ref_guide, lim=40.0):
    """joint_seat with the turn held at the arm file's own (+-lim deg), then a small free nudge (+-8 deg, no spin).
    The joint flat is found from the guide's current pose. Returns (T, turn, log)."""
    b, Ploc = setup(arm, guide); PP = prep(Ploc, 700); Ft = jframe(arm, guide); Fr = jframe(ref_arm, ref_guide)
    B = Ft @ np.linalg.inv(Fr); Mr = np.array(ref_guide.matrix_world); res = []
    for th in np.arange(-lim, lim + 0.1, 5.0):
        M = roll_about(Ft, th) @ B @ Mr; R, t = M[:3, :3], M[:3, 3]; t, best = _slide(b, PP, R, t, (0.8, 0.4, 0.2, 0.1))
        res.append((best, float(th), R, t))
    res.sort(key=lambda r: r[0])
    c0, th, R, t = res[0]; _, p0 = rest_cost(b, PP, R, t, True)
    R2, t2, c2 = _tnudge(b, PP, R, t); _, p2 = rest_cost(b, PP, R2, t2, True)
    T = np.eye(4); T[:3, :3] = R2; T[:3, 3] = t2
    return T, th, dict(cost_joint=round(c0, 3), parts_joint=p0, cost_nudged=round(c2, 3), parts_nudged=p2,
                       others=[(round(r[0], 3), r[1]) for r in res[1:5]], X=G.flat16(roll_about(Ft, th) @ B))


def swing_fit(b, P, F0, F1, step=3.0, keep=0.85):
    """carry outline points P (world, reference arm) allowing only the swing about the target's joint axis plus a shift.
    F0 / F1: joint-flat frames of reference / target arm. Returns (T, turn, score, shift mm)."""
    def dists(Q):
        d = np.empty(len(Q)); N = np.empty_like(Q)
        for k, q in enumerate(Q):
            loc, _n, _i, dist = b.find_nearest(Vector(q), 4.0)
            if loc is None: d[k] = 4.0; N[k] = q
            else: d[k] = dist; N[k] = loc
        return d, N
    B = F1 @ np.linalg.inv(F0); n = F1[:3, 2]; c = F1[:3, 3]; best = None
    for th in np.arange(-180, 180, step):
        Rr = G.rot(n, th); R = Rr @ B[:3, :3]; t = c + Rr @ (B[:3, 3] - c)
        d, _ = dists(P[::3] @ R.T + t); s = float(np.sqrt(np.mean(np.sort(d)[: int(len(d) * keep)] ** 2)))
        if best is None or s < best[0]: best = (s, th)
    s0, th0 = best
    for st in (1.0, 0.5, 0.25):
        cands = []
        for th in (th0 - st, th0, th0 + st):
            Rr = G.rot(n, th); R = Rr @ B[:3, :3]; t = c + Rr @ (B[:3, 3] - c)
            for _ in range(8):
                Q = P @ R.T + t; d, N = dists(Q); kp = d <= np.quantile(d, keep); t = t + (N[kp] - Q[kp]).mean(0)
            d, _ = dists(P @ R.T + t); s = float(np.sqrt(np.mean(np.sort(d)[: int(len(d) * keep)] ** 2)))
            cands.append((s, th, R, t))
        cands.sort(key=lambda x: x[0]); s0, th0, Rb, tb = cands[0]
    T = np.eye(4); T[:3, :3] = Rb; T[:3, 3] = tb
    return T, th0, s0, float(np.linalg.norm(tb - (c + G.rot(n, th0) @ (B[:3, 3] - c))))
